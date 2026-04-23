# License and Dependency Notes

This repo contains application code plus integrations with third-party services, models, and dependencies.

## Repository code

The code in this repository is released under the MIT License unless noted otherwise.

See [LICENSE](../LICENSE).

## Third-party model and service notes

### TribeV2

Narriv uses TribeV2 for local scoring.

- TribeV2 is not owned by this repository
- model weights and upstream code have their own license terms
- public materials for TribeV2 indicate `CC BY-NC 4.0`

Commercial use may be restricted. Review the upstream TribeV2 repository and license terms before using this stack in a paid product.

### OpenAI API

Narriv can use the OpenAI API for generation and refinement.

- OpenAI is an external API dependency
- usage is governed by OpenAI's terms and pricing
- model availability and preview/stable naming can change

Do not assume a preview model name is permanent.

### Hugging Face access

Some worker flows depend on Hugging Face-hosted assets and gated model dependencies.

- access may require `huggingface-cli login`
- `HF_TOKEN` may be required
- upstream asset terms still apply

## Publishing guidance

If you publish Narriv publicly, keep these statements explicit:

- the repository code is MIT-licensed
- third-party model weights are not re-licensed by this repository
- external API terms still apply
- TribeV2-based scoring is experimental and not a claim of real engagement prediction

## Commercial use warning

Do not assume the full stack is commercially clear just because this repository is MIT-licensed. The main licensing risk is upstream TribeV2 usage.
