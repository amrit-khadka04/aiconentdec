import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import uniform_filter


def _clip(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def compute_signals(pil: Image.Image) -> dict:
    img_gray = np.array(pil.convert("L"), dtype=float)
    img_rgb = np.array(pil.convert("RGB"), dtype=float)
    H, W = img_gray.shape

    # Pre-compute shared FFT (used by multiple signals below)
    fft_shifted = np.fft.fftshift(np.fft.fft2(img_gray))
    mag = np.abs(fft_shifted)
    cy, cx = H // 2, W // 2
    yy, xx = np.ogrid[:H, :W]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    r_max = min(cy, cx)

    # 1. texture_uniformity
    # Low local variation = smooth = AI (Farid & Lyu, 2003; Wang et al., 2020)
    lmean = uniform_filter(img_gray, 5)
    lsq = uniform_filter(img_gray ** 2, 5)
    lstd = np.sqrt(np.maximum(lsq - lmean ** 2, 0))
    texture_uniformity = 1.0 - _clip(lstd.mean() / 25.0)

    # 2. noise_level
    # Low noise = clean = AI (real cameras add sensor/shot noise)
    blur = np.array(
        pil.convert("L").filter(ImageFilter.GaussianBlur(2)), dtype=float
    )
    rms = np.sqrt(np.mean((img_gray - blur) ** 2))
    noise_level = 1.0 - _clip(rms / 12.0)

    # 3. frequency_artifact (FIXED — previous formula yielded ~1.0 for all images)
    # Spectral flatness in the mid-frequency band (15%–60% of max radius).
    # Natural images have a 1/f power spectrum concentrated at low frequencies
    # (peaky), so their mid-band spectral flatness is low.  AI-generated images
    # (especially diffusion models) produce a flatter, more uniform mid-band
    # energy distribution.  Higher flatness = more AI-like.
    # (Wang et al., 2020; Durall et al., 2020; Liu et al., 2022)
    r_lo, r_hi = r_max * 0.15, r_max * 0.60
    mid_mask = (dist >= r_lo) & (dist <= r_hi)
    if mid_mask.sum() > 0:
        mid_spectrum = mag[mid_mask]
        log_geom = float(np.mean(np.log(mid_spectrum + 1e-9)))
        arith = float(mid_spectrum.mean()) + 1e-9
        spectral_flatness = np.exp(log_geom) / arith  # 0–1; higher = flatter
        frequency_artifact = _clip(spectral_flatness * 1.8)
    else:
        frequency_artifact = 0.5

    # 4. color_uniformity
    # Low per-channel std dev = uniform colors = AI
    mean_std = float(np.mean([img_rgb[:, :, c].std() for c in range(3)]))
    color_uniformity = 1.0 - _clip(mean_std / 55.0)

    # 5. local_contrast_variance
    # Natural images show high variation in local Michelson contrast across regions.
    # AI/GAN images produce more spatially uniform contrast (Chai et al., 2020).
    # Low variance of block-level contrast = AI-like.
    block_size = max(8, min(H, W) // 8)
    contrasts = []
    for y in range(0, H - block_size + 1, block_size):
        for x in range(0, W - block_size + 1, block_size):
            block = img_gray[y : y + block_size, x : x + block_size]
            bmin, bmax = block.min(), block.max()
            contrasts.append((bmax - bmin) / (bmax + bmin + 1e-9))
    if len(contrasts) >= 4:
        local_contrast_variance = 1.0 - _clip(float(np.var(contrasts)) / 0.06)
    else:
        local_contrast_variance = texture_uniformity

    # 6. gradient_uniformity
    # Natural images have high spatial variance in gradient magnitude because
    # of real-world textures and edges. AI images tend to produce unnaturally
    # uniform gradients (too-smooth or too-sharp everywhere uniformly).
    # Low gradient std = overly uniform = AI-like.
    gx = np.gradient(img_gray, axis=1)
    gy = np.gradient(img_gray, axis=0)
    grad_mag = np.sqrt(gx ** 2 + gy ** 2)
    grad_uniformity = 1.0 - _clip(float(grad_mag.std()) / 30.0)

    # 7. spectral_irregularity (GAN fingerprint)
    # GAN transposed-convolution upsampling leaves checkerboard energy peaks at
    # the Nyquist corners of the 2-D FFT (Wang et al., 2020; Durall et al., 2020).
    # After fftshift, DC is at the centre — the four corners now hold the
    # highest-frequency (Nyquist) components.  We exclude the DC bin to avoid
    # it dominating the denominator.
    h8, w8 = max(1, H // 8), max(1, W // 8)
    corner_energy = (
        mag[:h8, :w8].sum()
        + mag[:h8, -w8:].sum()
        + mag[-h8:, :w8].sum()
        + mag[-h8:, -w8:].sum()
    )
    dc_mask = np.zeros((H, W), dtype=bool)
    dc_mask[cy, cx] = True
    non_dc_total = mag[~dc_mask].sum() + 1e-9
    spectral_irregularity = _clip((corner_energy / non_dc_total) * 8.0)

    # 8. saturation_variance
    # Real photographs exhibit a wide spread of saturation values; AI-generated
    # images often compress the saturation range (over-processed look).
    # Low saturation variance = compressed = AI-like.
    r_c = img_rgb[:, :, 0] / 255.0
    g_c = img_rgb[:, :, 1] / 255.0
    b_c = img_rgb[:, :, 2] / 255.0
    cmax = np.maximum.reduce([r_c, g_c, b_c])
    cmin = np.minimum.reduce([r_c, g_c, b_c])
    saturation = np.where(cmax > 0, (cmax - cmin) / (cmax + 1e-9), 0.0)
    saturation_variance = 1.0 - _clip(float(saturation.std()) / 0.30)

    # 9. regional_noise_inconsistency (NEW)
    # AI-composited or partially-generated images often exhibit spatially
    # inconsistent noise: the subject (face/object) may have different high-
    # frequency noise characteristics than the background.  We divide the image
    # into quadrants and measure the coefficient of variation (CV) of noise
    # across them.  High CV = inconsistent noise = compositing artifact.
    # (Rossler et al., 2019; Chen et al., 2022)
    rh, rw = max(1, H // 2), max(1, W // 2)
    quad_regions = [
        img_gray[:rh, :rw],
        img_gray[:rh, rw:],
        img_gray[rh:, :rw],
        img_gray[rh:, rw:],
    ]
    quad_noise = []
    for region in quad_regions:
        if region.size > 0:
            region_blur = uniform_filter(region, 3)
            quad_noise.append(float(np.sqrt(np.mean((region - region_blur) ** 2))))
    if len(quad_noise) >= 4 and np.mean(quad_noise) > 0:
        noise_cv = float(np.std(quad_noise)) / (float(np.mean(quad_noise)) + 1e-9)
        # Normalise: CV > 0.55 = very inconsistent noise (compositing artefact).
        # Empirically, natural photographs have CV ≈ 0.10–0.35.
        regional_noise_inconsistency = _clip(noise_cv / 0.55)
    else:
        regional_noise_inconsistency = 0.0

    # 10. radial_spectral_slope (NEW)
    # Natural images obey a 1/f^α power law (α ≈ 2–3) in the frequency domain.
    # AI-generated images — particularly from diffusion models — deviate from
    # this natural spectral law.  GAN images produce flatter slopes (α closer
    # to -1) due to transposed-convolution upsampling; diffusion models can
    # produce either flatter or steeper deviations.  We fit the log-log slope
    # of radial power vs frequency and penalise deviation from the natural range.
    # (Torralba & Oliva, 2003; Durall et al., 2020; Liu et al., 2024)
    mag_sq = mag ** 2
    n_bins = min(32, max(4, r_max // 4))
    ring_powers = []
    ring_radii = []
    bin_edges = np.linspace(2.0, r_max * 0.70, n_bins + 1)
    for i in range(n_bins):
        r1, r2 = bin_edges[i], bin_edges[i + 1]
        ring_mask = (dist >= r1) & (dist < r2)
        if ring_mask.sum() > 0:
            ring_powers.append(float(mag_sq[ring_mask].mean()))
            ring_radii.append(float((r1 + r2) / 2))
    if len(ring_powers) >= 4:
        log_r = np.log(np.array(ring_radii))
        log_p = np.log(np.array(ring_powers) + 1e-9)
        slope = float(np.polyfit(log_r, log_p, 1)[0])
        # Natural range: α ≈ -2.0 to -3.0 (midpoint -2.5, tolerance ±0.8).
        # Slopes outside [-3.3, -1.7] indicate synthetic content; scale by 1.5
        # so that a slope of 0 (flat/white-noise-like) gives a full score of 1.0.
        deviation = max(0.0, abs(slope - (-2.5)) - 0.8)
        radial_spectral_slope = _clip(deviation / 1.5)
    else:
        radial_spectral_slope = 0.0

    return {
        "texture_uniformity": round(texture_uniformity, 3),
        "noise_level": round(noise_level, 3),
        "frequency_artifact": round(frequency_artifact, 3),
        "color_uniformity": round(color_uniformity, 3),
        "local_contrast_variance": round(local_contrast_variance, 3),
        "gradient_uniformity": round(grad_uniformity, 3),
        "spectral_irregularity": round(spectral_irregularity, 3),
        "saturation_variance": round(saturation_variance, 3),
        "regional_noise_inconsistency": round(regional_noise_inconsistency, 3),
        "radial_spectral_slope": round(radial_spectral_slope, 3),
    }
