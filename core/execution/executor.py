# core/execution/executor.py
import subprocess, tempfile, os, resource, time
from dataclasses import dataclass
from typing import List

LANGUAGE_CONFIG = {
    "python":     {"ext": "py",   "cmd": ["python3", "{file}"]},
    "javascript": {"ext": "js",   "cmd": ["node",    "{file}"]},
    "java":       {"ext": "java", "cmd": ["java", "-cp", "{dir}", "Solution"]},
    "cpp":        {"ext": "cpp",
                   "compile": ["g++", "-O2", "-o", "{bin}", "{file}"],
                   "cmd":     ["{bin}"]},
}

@dataclass
class TestResult:
    test_case_id:  str
    status:        str    # accepted | wrong_answer | time_limit | runtime_error | compilation_error
    stdout:        str
    stderr:        str
    time_ms:       float
    is_public:     bool


def run_code_challenge(code: str, language: str, test_cases,
                       time_limit_s: int = 5, memory_mb: int = 128) -> List[TestResult]:
    config  = LANGUAGE_CONFIG.get(language)
    if not config:
        raise ValueError(f"Unsupported language: {language}")

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        ext      = config["ext"]
        src_path = os.path.join(tmpdir, f"solution.{ext}")
        bin_path = os.path.join(tmpdir, "solution")

        with open(src_path, "w") as f:
            f.write(code)

        # Compile step (C++ / Java)
        if "compile" in config:
            compile_cmd = [
                p.replace("{file}", src_path)
                 .replace("{bin}",  bin_path)
                 .replace("{dir}",  tmpdir)
                for p in config["compile"]
            ]
            cp = subprocess.run(compile_cmd, capture_output=True, timeout=20)
            if cp.returncode != 0:
                return [
                    TestResult(tc.id, "compilation_error", "",
                               cp.stderr.decode(errors="replace"), 0, tc.is_public)
                    for tc in test_cases
                ]

        for tc in test_cases:
            run_cmd = [
                p.replace("{file}", src_path)
                 .replace("{bin}",  bin_path)
                 .replace("{dir}",  tmpdir)
                for p in config["cmd"]
            ]

            t0 = time.perf_counter()
            try:
                proc = subprocess.run(
                    run_cmd,
                    input=tc.stdin.encode(),
                    capture_output=True,
                    timeout=time_limit_s,
                    preexec_fn=lambda: _apply_limits(memory_mb, time_limit_s),
                )
                elapsed = round((time.perf_counter() - t0) * 1000, 2)

                actual   = proc.stdout.decode(errors="replace").strip()
                expected = tc.expected_stdout.strip()

                if proc.returncode != 0:
                    status = "runtime_error"
                elif actual == expected:
                    status = "accepted"
                else:
                    status = "wrong_answer"

                results.append(TestResult(
                    tc.id, status, actual,
                    proc.stderr.decode(errors="replace"),
                    elapsed, tc.is_public
                ))

            except subprocess.TimeoutExpired:
                results.append(TestResult(tc.id, "time_limit", "", "", time_limit_s * 1000, tc.is_public))

    return results


def _apply_limits(memory_mb: int, time_limit_s: int):
    try:
        mem = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    except (ValueError, resource.error):
        pass  # RLIMIT_AS not supported on macOS
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (time_limit_s, time_limit_s))
    except (ValueError, resource.error):
        pass