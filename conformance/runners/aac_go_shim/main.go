// Differential-testing shim: read one JSON object per line from stdin, print
// ComputeCapsuleID for each. Uses ONLY the AAC Go canonicalizer, which is an
// independent implementation of the same rules (own utf16 key comparison, own
// escaping, own number handling) rather than a copy of the Python one.
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/action-state-group/agent-action-capsule/go/canonical"
)

// decodeWithNumbers mirrors verify.DecodeCapsuleJSON and cmd/vector_runner:
// UseNumber, so JSON integers arrive as json.Number rather than float64.
// Without this every integer reaches the canonicalizer as a float and is
// refused by the float guard -- which is a defect in THIS shim, not in the
// canonicalizer, and is exactly what a first version of this file got wrong.
func decodeWithNumbers(data []byte) (map[string]interface{}, error) {
	d := json.NewDecoder(strings.NewReader(string(data)))
	d.UseNumber()
	var v map[string]interface{}
	if err := d.Decode(&v); err != nil {
		return nil, err
	}
	return v, nil
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1024*1024), 1024*1024)
	for sc.Scan() {
		line := sc.Bytes()
		if len(line) == 0 {
			continue
		}
		v, err := decodeWithNumbers(line)
		if err != nil {
			fmt.Println("PARSE_ERROR")
			continue
		}
		id, cerr := canonical.ComputeCapsuleID(v)
		if cerr != nil {
			fmt.Printf("REFUSED:%T\n", cerr)
			continue
		}
		fmt.Println(id)
	}
}
