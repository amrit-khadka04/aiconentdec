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
    # Low local variation = smooth = AI
    lmean = uniform_filter(img_gray, 5)
    lsq = uniform_filter(img_gray ** 2, 5)
    lstd = np.sqrt(np.maximum(lsq - lmean ** 2, 0))
    texture_uniformity = 1.0 - _clip(lstd.mean() / 30.0)

    # 2. noise_level
    # Low noise = clean = AI
    blur = np.array(
        pil.convert("L").filter(ImageFilter.GaussianBlur(2)), dtype=float
    )
    rms = np.sqrt(np.mean((img_gray - blur) ** 2))
    noise_level = 1.0 - _clip(rms / 15.0)

    # 3. frequency_artifact
    # FFT, measure high-freq energy ratio
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

    return {
        "texture_uniformity": round(texture_uniformity, 3),
        "noise_level": round(noise_level, 3),
        "frequency_artifact": round(frequency_artifact, 3),
        "color_uniformity": round(color_uniformity, 3),
    }
