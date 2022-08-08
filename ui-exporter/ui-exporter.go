package main

import (
  "bytes"
  "compress/gzip"
  // "os/exec"
  "strconv"
  "strings"
  "errors"
  "github.com/PuerkitoBio/goquery"
  "github.com/yosssi/gohtml"
  "github.com/ditashi/jsbeautifier-go/jsbeautifier"
  "fmt"
  "io"
  "io/ioutil"
  "log"
  "os"
)

const chunkSize = 4096
var hasJsBeautifier = true

func main() {
    path := "diabotical.exe"
    fmt.Println("File:", path)

    file, err := os.Open(path)
    if err != nil {
        log.Fatal("Error while opening file", err)
    }

    defer file.Close()

  // look for gzip headers in binary
    search := []byte{0x1f, 0x8b, 0x08}
    offsets, _ := findAll(file, search)

    for i, offset := range offsets {
      processFile(file, i, offset)
      // fmt.Println("Offset:", offset)
    }
}

func processFile(file *os.File, i int, offset int64) {
    // move to gzip header offset
    _, err := file.Seek(offset, 0)
    if err != nil {
        log.Fatal(err)
    }

    // read rest of file into outBuffer and newly created file
    buf := make([]byte, 1024)
  outBuffer := bytes.NewBuffer(make([]byte, 0))

    for {
      n, err := file.Read(buf)
      if err == io.EOF {
        break
      }

      if err != nil {
        log.Fatal(err)
      }

      if n > 0 {
        outBuffer.Write(buf[:n])
      }
    }

    // decompress outBuffer
    gr, err := gzip.NewReader(outBuffer)
    if err != nil {
      // fmt.Println("err h1")
      log.Fatal(err)
    }
    defer gr.Close()

    // Read data
    // we just ignore errors here, as this will error because of unknown gz length
    decompressedBytes, _ := ioutil.ReadAll(gr)

    // create out file
    outFile, err := os.Create(gr.Header.Name)
    if err != nil {
        log.Fatal(err)
    }
    defer outFile.Close()

  // beautify the html
    s := gohtml.Format(string(decompressedBytes))

    // write out file
    _, err = outFile.WriteString(s)
    if err != nil {
        log.Fatal(err)
    }

    // Load the HTML document
    r := strings.NewReader(s)
    doc, err := goquery.NewDocumentFromReader(r)
    if err != nil {
      log.Fatal(err)
    }

    // create folder
    folderName := strings.Split(gr.Header.Name, ".")[0]
    err = os.Mkdir(folderName, 0755)
    if err != nil {
        log.Fatal(err)
    }

    // find script tags and write their contents to files
    doc.Find("script").Not("script[type]").Each(func(i int, s *goquery.Selection) {
      // create out file
      filePath := folderName + "/" + strconv.Itoa(i) + ".js"
      outFile, err := os.Create(filePath)
      if err != nil {
          log.Fatal(err)
      }
      defer outFile.Close()

      outString := s.Text()

      options := jsbeautifier.DefaultOptions()
      outFormatedString, err := jsbeautifier.Beautify(&outString, options)
      if err != nil {
          log.Fatal(err)
      }

      _, err = outFile.WriteString(outFormatedString)
      if err != nil {
          log.Fatal(err)
      }

      // external beautify
      // if (hasJsBeautifier) {
      //  cmd := exec.Command("js-beautify", "-r", filePath)
      //  err = cmd.Run()
      //  if err != nil {
      //      hasJsBeautifier = false
      //      log.Println("Couldn't find js-beautify, so javascript is not beautified")
      //      log.Println("To install: npm -g install js-beautify")
      //      log.Println("See: https://github.com/beautify-web/js-beautify")
      //      // log.Fatal(err)
      //  }
      // }
    })

}

func find(r io.ReaderAt, search []byte) (int64, error) {
    var offset int64
  chunk := make([]byte, chunkSize+len(search))

  for {
    n, err := r.ReadAt(chunk, offset)
    idx := bytes.Index(chunk[:n], search)

    if idx >= 0 {
      return offset + int64(idx), nil
    }

    if err == io.EOF {
      break
    } else if err != nil {
      return -1, err
    }

    offset += chunkSize
  }

  return -1, errors.New("not found")
}

func findAll(r io.ReaderAt, search []byte) ([]int64, error) {
    var offset int64
    var out []int64
  chunk := make([]byte, chunkSize+len(search))

  for {
    n, err := r.ReadAt(chunk, offset)
    idx := bytes.Index(chunk[:n], search)

    if idx >= 0 {
      out = append(out, offset + int64(idx))
        // fmt.Println("Offset:", offset + int64(idx))
    }

    if err == io.EOF {
      break
    } else if err != nil {
      return nil, err
    }

    offset += chunkSize
  }

  return out, nil
}