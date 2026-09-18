# FlashVSR API — Python client

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![Hosted on Synexa](https://img.shields.io/badge/hosted%20on-Synexa-6366f1.svg)](https://synexa.ai/explore/bytedance/seedvr2-upscale)

FlashVSR is a one-step, streaming video super-resolution model from OpenImagingLab that brings diffusion-quality upscaling close to real time. This package is a FlashVSR-style super-resolution API client for Python: one `pip install` gives you diffusion-based upscaling and restoration as an HTTPS call, with no weights to download and no GPU to provision.

You get a blocking `run()` that returns the upscaled output URL, a submit-and-poll path for large batches, webhook delivery on completion, and one runtime dependency (`httpx`). It is meant for media pipelines, archive restoration and product features that need higher-resolution frames and stills without owning the inference stack.

> **Try it now:** [https://synexa.ai/explore/bytedance/seedvr2-upscale](https://synexa.ai/explore/bytedance/seedvr2-upscale) — the hosted model behind this client. New accounts get a free trial credit.

## Contents

- [Why this client](#why-this-client)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Hosted models](#hosted-models)
- [Parameters](#parameters)
- [Advanced usage](#advanced-usage)
- [About FlashVSR](#about-flashvsr)
- [Use cases](#use-cases)
- [FAQ](#faq)
- [License](#license)

## Why this client

- **No GPU to provision.** FlashVSR is distilled from a Wan-family video diffusion model and its headline throughput figures are measured on an A100. The hosted endpoint runs on managed GPUs.
- **No environment to maintain.** No custom sparse-attention kernels to build, no CUDA/PyTorch version matching, no multi-gigabyte checkpoints. Install, set a key, call `run()`.
- **No cold starts on your side.** Loading a video diffusion model takes tens of seconds and keeping it warm costs money around the clock. Here you pay per prediction only.
- **Very low cost per image.** `bytedance/seedvr2-upscale` is $0.004 per run, so restoring a thousand frames costs about $4.

## Installation

```bash
pip install git+https://github.com/flashvsr/flashvsr-api.git
```

Then set your API key (create one at [synexa.ai](https://synexa.ai)):

```bash
export SYNEXA_API_KEY="sk-..."
```

## Quickstart

```python
import flashvsr_api

output = flashvsr_api.run({
    "image_url": "https://example.com/input.png"
})
print(output)   # URL(s) of the generated result
```

Or with an explicit client:

```python
from flashvsr_api import Client

client = Client(api_key="sk-...")
output = client.run({"image_url": "https://example.com/input.png"})
```

## Hosted models

| Model | Category | What it does | Price / run |
|---|---|---|---|
| [`bytedance/seedvr2-upscale`](https://synexa.ai/explore/bytedance/seedvr2-upscale) | super-resolution | SeedVR2 restores and upscales images, recovering detail rather than simply interpolating pixels. | $0.004 |

The default model is **`bytedance/seedvr2-upscale`**; pass `model="owner/name"` to `run()` to use another one from the table.

## Parameters

### `bytedance/seedvr2-upscale`

| Field | Type | Required | Default | Range | Description |
|---|---|---|---|---|---|
| `image_url` | file | yes | — | — | Image to upscale (.jpg/.png/.webp) |
| `upscale_mode` | string | no | `factor` | target, factor | The mode to use for the upscale. If 'target', the upscale factor will be calculated based on the target resolution. If 'factor', the upscale factor will be used directly. |
| `upscale_factor` | number | no | `2` | 1, 10 | Upscaling factor to be used. Will multiply the dimensions with this factor when `upscale_mode` is `factor`. |
| `target_resolution` | string | no | `1080p` | 720p, 1080p, 1440p, 2160p | The target resolution to upscale to when `upscale_mode` is `target`. |
| `seed` | integer | no | `random` | — | The random seed used for the generation process. |
| `noise_scale` | number | no | `0.1` | 0, 1 | The noise scale to use for the generation process. |
| `output_format` | string | no | `jpg` | png, jpg, webp | The format of the output image. |

## Advanced usage

**Submit without blocking, then poll:**

```python
prediction = client.run(input, wait=False)      # returns immediately
prediction = client.wait(prediction, timeout=300)
print(prediction["output"])
```

**Webhook on completion:**

```python
client.run(input, wait=False, webhook="https://your-app.example/hooks/synexa")
```

**Errors:**

```python
from flashvsr_api import ModelError, PredictionTimeout

try:
    output = client.run(input)
except ModelError as e:
    print("failed:", e, e.prediction and e.prediction.get("id"))
except PredictionTimeout:
    print("still running — poll later")
```

Status values you will see on a prediction: `starting` → `processing` → `succeeded` | `failed`.

## About FlashVSR

FlashVSR is described in *FlashVSR: Towards Real-Time Diffusion-Based Streaming Video Super-Resolution* from OpenImagingLab (Shanghai AI Laboratory), released in 2025. Its goal is to keep the detail-recovery quality of diffusion-based super-resolution while removing the two things that make it impractical for video: multi-step sampling and full attention over long frame windows.

Three design choices do the work. The model is distilled into a single denoising step using a multi-stage distillation pipeline, so each frame is produced in one forward pass. Attention is made locality-constrained and block-sparse, which keeps compute bounded as resolution grows. And a small conditional decoder replaces the heavy VAE decoder, cutting the cost of turning latents back into pixels. The model runs in a streaming fashion over the input, so it can process arbitrarily long clips with bounded memory. The authors report around 17 frames per second at 768×1408 on a single A100.

Typical output is a 4× upscale of the input video with recovered texture rather than interpolated blur. Limits: like all generative upscalers it can invent detail that was not in the source, it is trained for natural video degradations rather than text or line art, and self-hosting still needs a data-centre class GPU.

The hosted endpoint used by this client is `bytedance/seedvr2-upscale`, which provides the same diffusion-based restoration and upscaling capability; it serves ByteDance's SeedVR2, a one-step diffusion restoration model. Note that this endpoint takes a single image (`image_url`) and returns an upscaled image; it does not accept a video file, so for video you upscale extracted frames and reassemble them, without the temporal consistency FlashVSR's streaming design provides. The original FlashVSR weights are available at https://github.com/OpenImagingLab/FlashVSR if you want to self-host.

**Official project:** https://github.com/OpenImagingLab/FlashVSR

## Use cases

- **Upscale thumbnails and stills** — call `run({"image_url": url, "upscale_mode": "factor", "upscale_factor": 2})` on low-resolution assets before publishing.
- **Restore archive frames** — extract frames from an old clip, upscale each with `wait=False`, and reassemble at the original frame rate.
- **Hit a fixed output size** — use `upscale_mode="target"` with `target_resolution` to normalise a mixed catalogue to one resolution.
- **Clean up AI-generated images** — pass a 512 px generation through the endpoint to recover detail and sharpen edges at print size.
- **Prepare training data** — upscale a small dataset to a common resolution at $4 per thousand images.
- **Reproducible pipelines** — fix `seed` and `noise_scale` so repeated runs on the same input produce identical output.

## FAQ

**Is there a FlashVSR API?**

Not from the original authors; FlashVSR is released as open weights. This client exposes the same diffusion-based super-resolution capability through a hosted endpoint (`bytedance/seedvr2-upscale`) that you call over HTTPS. The hosted endpoint works on single images.

**How much does the FlashVSR API cost?**

The hosted `bytedance/seedvr2-upscale` model is $0.004 per run. Billing is per prediction; there is no hourly GPU charge.

**Can I run FlashVSR without a GPU?**

With this client, yes: inference runs on the hosted service and your code only makes HTTP requests. Self-hosting FlashVSR needs a CUDA GPU; the authors' throughput figures are for an A100.

**Does this client work with the original FlashVSR repo or ComfyUI?**

No. It does not load the OpenImagingLab/FlashVSR checkpoints and it is not a ComfyUI node. It is a network client for the hosted endpoint. If you need FlashVSR's streaming video pipeline itself, run the official repository locally.

**What input formats does it accept?**

A publicly reachable image URL (`image_url`) in .jpg, .png or .webp. Optional fields: `upscale_mode` (`factor` or `target`), `upscale_factor`, `target_resolution`, `seed`, `noise_scale` and `output_format`. The output is a URL to the upscaled image. Video files are not accepted; upscale frames individually.

**Is this the official FlashVSR SDK?**

No. This is an independent, community-maintained client and is not affiliated with OpenImagingLab or ByteDance. The official project lives at https://github.com/OpenImagingLab/FlashVSR.

## Related

- [FlashVSR (official repository)](https://github.com/OpenImagingLab/FlashVSR) — paper, weights and streaming inference code.
- [Synexa Python client](https://github.com/synexa-ai/synexa-python) — the general-purpose client this package wraps.
- [bytedance/seedvr2-upscale](https://synexa.ai/explore/bytedance/seedvr2-upscale) — the hosted SeedVR2 restoration and upscaling endpoint behind this client.

## License

MIT. This is an independent, community-maintained client and is not affiliated with or endorsed by the authors of FlashVSR. Model weights and trademarks belong to their respective owners.
