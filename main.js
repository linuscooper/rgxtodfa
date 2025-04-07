let pyodide = null;
let regexPattern = '';
let dfaChecker = null;

async function loadPyodideAndPackages() {
  pyodide = await loadPyodide();
  const code = await (await fetch("rgxtodfa.py")).text();
  await pyodide.runPythonAsync(code);
}

loadPyodideAndPackages();

document.getElementById("convert-btn").addEventListener("click", async () => {
  regexPattern = document.getElementById("regex-input").value.trim();
  document.getElementById("test-passwords").innerHTML = "";
  if (!regexPattern) return;

  const code = `
rgx = parse_regex(r"""${regexPattern}""")
rtd = generate_nodes(rgx)
dot = dfa_to_dot(rtd, rgx)
`;

  try {
    await pyodide.runPythonAsync(code);
    const dot = pyodide.globals.get("dot");
    const viz = new Viz();
    const svg = await viz.renderSVGElement(dot);
    document.getElementById("dfa-visualization").innerHTML = "";
    document.getElementById("dfa-visualization").appendChild(svg);
    document.getElementById("viz-container").style.display = "block";
    document.getElementById("test-container").style.display = "block";
    await pyodide.runPythonAsync(`
    def check_string(input_str):
        start_node = next(node for node in rtd if repr(node.r) == repr(rgx))
        current = start_node
        
        try:
            for c in input_str:
                if c not in current.transitions:
                    return False
                current = current.transitions[c]
            return current.is_accepting
        except Exception as e:
            print(f"Error: {e}")
            return False
    `);
    dfaChecker = pyodide.globals.get("check_string");
    document.getElementById("status-message").textContent = "";
  } catch (err) {
    console.error(err);
    document.getElementById("status-message").textContent = "Conversion failed: " + err;
    document.getElementById("status-message").className = "status error";
  }
});

document.getElementById("add-test-btn").addEventListener("click", async () => {
  const testStr = document.getElementById("test-input").value;
  if (!testStr || !dfaChecker) return;
  try {
    const accepted = dfaChecker(testStr);
    const testList = document.getElementById("test-passwords");
    const div = document.createElement("div");
    div.className = "test-case";
    div.innerHTML = `
      <input type="text" value="${testStr}" readonly />
      <div class="test-result ${accepted ? "pass" : "fail"}">${accepted ? "✔" : "✖"}</div>
    `;
    testList.appendChild(div);
  } catch (e) {
    alert("Error testing string: " + e);
  }
});

document.getElementById("clear-btn").addEventListener("click", () => {
  document.getElementById("regex-input").value = "";
  document.getElementById("dfa-visualization").innerHTML = "<p>Convert a regex pattern to see its DFA visualization</p>";
  document.getElementById("viz-container").style.display = "none";
  document.getElementById("test-passwords").innerHTML = "";
  document.getElementById("test-input").value = "";
  document.getElementById("test-container").style.display = "none";
});

document.querySelectorAll(".example-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.getElementById("regex-input").value = btn.dataset.pattern;
  });
});

