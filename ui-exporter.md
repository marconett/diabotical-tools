# ui-exporter

Exports the UI (HTML / JS / CSS) from a given `diabotical.exe`

The UI currently shows up at 3 different points in the `diabotical.exe`, as:

* `editpad_gf`
* `hud`
* `index`

Each is one big `.html` file containing HTML, JS and CSS. As far as I can tell, the files are more or less the same.

The Javascript part is the most interesting. The devs put each source JS file inside its own `<script>` tag. This tool parses the HTML files, exports the content of each `<script>` tag, prettifies the code and puts into its own `.js` file. This effectively reverses the build process.

This is written in Go, but I am not providing binaries of this tool at this time.

## Usage

```
# copy diabltical.exe into the same directory as ui-exporter.go
go get
go run ui-exporter.go
```