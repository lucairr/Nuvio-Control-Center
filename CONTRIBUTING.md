# Contributing

Contributions and LG webOS compatibility reports are welcome. This is an independent community project and **does not contain Nuvio TV's proprietary account configuration or keys**.

1. Create an issue describing OS, webOS version, Nuvio version, CLI version and a **sanitized** error log.
2. Fork the repository and create a feature branch.
3. Run `python -m unittest discover -s tests -v` and add/modify tests for code changes.
4. Keep dependencies to a minimum; never add an endpoint for arbitrary shell execution.
5. Do not commit generated state, config, auth hashes, `.ssh` keys, or downloaded IPKs.

UI language: Italian in this initial beta. Translations and accessibility improvements are welcome.
