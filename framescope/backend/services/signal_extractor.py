import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import uniform_filter


def _clip(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def compute_signals(pil: Image.Image) -> dict:
    img_gray = np.array(pil.convert("L"), dtype=float)
    img_rgb = np.array(pil.convert("RGB"), dtype=float)
    H, W = img_gray.shape

    # 1. texture_uniformity
    # Low local variation = smooth = AI (Farid & Lyu, 2003; Wang et al., 2020)
    lmean = uniform_filter(img_gray, 5)
    lsq = uniform_filter(img_gray ** 2, 5)
    lstd = np.sqrt(np.maximum(lsq - lmean ** 2, 0))
    texture_uniformity = 1.0 - _clip(lstd.mean() / 30.0)

    # 2. noise_level
    # Low noise = clean = AI (real cameras add sensor/shot noise)
    blur = np.array(
        pil.convert("L").filter(ImageFilter.GaussianBlur(2)), dtype=float
    )
    rms = np.sqrt(np.mean((img_gray - blur) ** 2))
    noise_level = 1.0 - _clip(rms / 15.0)

    # 3. frequency_artifact
    # FFT high-freq energy ratio; GAN artifacts elevate this (Frank et al., 2020)
    fft = np.fft.fftshift(np.fft.fft2(img_gray))
    mag = np.abs(fft)
    cy, cx = H // 2, W // 2
    r = min(H, W) // 6
    yy, xx = np.ogrid[:H, :W]
    center = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
    hf_ratio = mag[~center].sum() / (mag.sum() + 1e-9)
    frequency_artifact = _clip(hf_ratio * 2.5)

    # 4. color_uniformity
    # Low per-channel std dev = uniform colors = AI
    mean_std = float(np.mean([img_rgb[:, :, c].std() for c in range(3)]))
    color_uniformity = 1.0 - _clip(mean_std / 60.0)

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
        local_contrast_variance = 1.0 - _clip(float(np.var(contrasts)) / 0.08)
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
    grad_uniformity = 1.0 - _clip(float(grad_mag.std()) / 35.0)

    # 7. spectral_irregularity (GAN fingerprint)
    # GAN transposed-convolution upsampling leaves checkerboard energy peaks at
    # the Nyquist corners of the 2-D FFT (Wang et al., 2020; Durall et al., 2020).
    # After fftshift, DC is at the centre — the four corners now hold the
    # highest-frequency (Nyquist) components.  We exclude the DC bin to avoid
    # it dominating the denominator.
    # `mag` (already computed above) = |fftshift(fft2(img_gray))|
    h8, w8 = max(1, H // 8), max(1, W // 8)
    corner_energy = (
        mag[:h8, :w8].sum()
        + mag[:h8, -w8:].sum()
        + mag[-h8:, :w8].sum()
        + mag[-h8:, -w8:].sum()
    )
    # Exclude the dominant DC component at the centre
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
    saturation_variance = 1.0 - _clip(float(saturation.std()) / 0.35)

    return {
        "texture_uniformity": round(texture_uniformity, 3),
        "noise_level": round(noise_level, 3),
        "frequency_artifact": round(frequency_artifact, 3),
        "color_uniformity": round(color_uniformity, 3),
        "local_contrast_variance": round(local_contrast_variance, 3),
        "gradient_uniformity": round(grad_uniformity, 3),
        "spectral_irregularity": round(spectral_irregularity, 3),
        "saturation_variance": round(saturation_variance, 3),
    }
