# Vendored dependencies

`plugins/kiutils` and `plugins/easyeda2kicad` used to be git submodules and are now
vendored directly into this repository. They were imported at these upstream commits:

| Path                     | Upstream                                          | Commit    | Version        |
| ------------------------ | ------------------------------------------------- | --------- | -------------- |
| `plugins/kiutils`        | https://github.com/Steffen-W/kiutils.git          | `8168b1d` | v1.4.9-5       |
| `plugins/easyeda2kicad`  | https://github.com/Steffen-W/easyeda2kicad.py.git | `f193d36` | v1.0.1-11      |

To update one of them, pull the upstream changes into a scratch clone and copy the
tree over the directory here, then update the commit in this table.
