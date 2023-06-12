import os
import secrets
from zoofc1.lexer import splitSource, tokenize, TT


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
SOURCE_CODE_DIR = os.path.join(THIS_DIR, "zoofc1")
SNIPPET_DIR = os.path.join(THIS_DIR, "snippets")


class ErrorCode:
    def __init__(self, code, filename, linenr):
        self.code = code
        self.filename = filename
        self.linenr = linenr
        self.invalid = ""


def collect_error_codes_from_source():
    """Find all error codes in the source."""

    error_codes = []
    all_codes = set()

    for fname in os.listdir(SOURCE_CODE_DIR):
        if not fname.endswith((".zf", ".py")):
            continue

        filename = os.path.join(SOURCE_CODE_DIR, fname)
        with open(filename, "rb") as f:
            text = f.read().decode()

        for linenr, line in enumerate(text.splitlines(), start=1):
            i = 0
            while True:
                i = line.find('"E', i)
                if i < 0:
                    break
                i2 = line.find('"', i + 1)
                assert i2 > i
                s = line[i + 1 : i2]
                i = i2
                if 3 <= len(s) <= 6 and any(c.isnumeric() for c in s[1:]):
                    # String looks close enough!
                    ec = ErrorCode(s, filename, linenr)
                    error_codes.append(ec)
                    if not all(c.isnumeric() for c in s[1:]):
                        ec.invalid = "not numeric"
                    elif len(s) != 5:
                        ec.invalid = "incorrect length"
                    elif s.endswith("000"):
                        ec.invalid = "is placeholder"
                    elif s in all_codes:
                        ec.invalid = "duplicate"
                    else:
                        all_codes.add(s)

    return error_codes


def collect_error_codes_from_snippets():
    """Find a set of error codes from the snippet outputs."""

    all_codes = set()

    for fname in os.listdir(SNIPPET_DIR):
        if not fname.endswith(".zf"):
            continue
        filename = os.path.join(SNIPPET_DIR, fname)
        with open(filename, "rb") as f:
            text = f.read().decode()

        i = 0
        while True:
            i = text.find("Error (E", i)
            if i < 0:
                break
            i2 = text.find(") --", i + 8)
            assert i2 > i
            s = text[i + 7 : i2]
            i = i2
            all_codes.add(s)

    return all_codes


# %% Tests


def test_error_numbers_are_valid_and_unique():
    error_codes = collect_error_codes_from_source()

    print(f"Found {len(error_codes)} error codes.")
    for ec in error_codes:
        if ec.invalid:
            print(
                f'Invalid ({ec.invalid}): {ec.code} in "{ec.filename}", line {ec.linenr}'
            )

    assert len(error_codes) > 32
    assert not any(ec.invalid for ec in error_codes)


def test_error_codes_appear_in_correct_file():
    error_codes = collect_error_codes_from_source()

    for ec in error_codes:
        firstnum = int(ec.code[1])
        fname = os.path.basename(ec.filename)
        if firstnum == 1:
            assert fname in ("parser.py")
        elif firstnum == 2:
            assert fname in ("resolver.py", "errors.py")
        elif firstnum == 8:
            assert fname in ("interpreter.py", "errors.py")
        else:
            assert False, f"Unknown erorr code prefix {ec.code}"


def test_that_each_error_code_is_in_a_snippet():
    excludes = {"E0000"}

    error_codes = collect_error_codes_from_source()
    source_codes = {ec.code for ec in error_codes if not ec.invalid}

    snippet_codes = collect_error_codes_from_snippets()

    unknown_codes = snippet_codes.difference(source_codes)
    untested_codes = source_codes.difference(snippet_codes)
    untested_codes.difference_update(excludes)

    if unknown_codes:
        print("Unknown codes:", unknown_codes)
    if untested_codes:
        print("Untested codes:", untested_codes)

    assert not unknown_codes
    assert not untested_codes


# %% Manual stuff


def zero_out_all_codes():
    """Set all error codes to placeholder codes."""
    error_codes = collect_error_codes_from_source()
    assigned_count = 0

    for ec in error_codes:
        if not ec.code.endswith("000"):
            prefix = ec.code[:2]
            new_code = prefix + "000"

            assigned_count += 1
            _replace_error_code(ec, new_code)

    print(f"Zeroed out {assigned_count} error codes.")


def assign_error_codes():
    """Assign a new random error code to each placeholder.
    Call this function manually.
    """

    error_codes = collect_error_codes_from_source()
    all_codes = {ec.code for ec in error_codes if not ec.invalid}
    assigned_count = 0

    for ec in error_codes:
        if ec.code.endswith("000"):
            prefix = ec.code[:2]
            valid_codes = set([f"{prefix}{i:03d}" for i in range(1, 1000)])
            valid_codes.difference_update(all_codes)
            new_code = secrets.choice(list(valid_codes))

            assigned_count += 1
            all_codes.add(new_code)
            _replace_error_code(ec, new_code)

    print(f"Assigned {assigned_count} error codes.")


def _replace_error_code(ec, new_code):
    with open(ec.filename, "rb") as f:
        text = f.read().decode()
        lines = text.split("\n")
        lines[ec.linenr - 1] = lines[ec.linenr - 1].replace(ec.code, new_code)
        text = "\n".join(lines)
        with open(ec.filename, "wb") as f:
            f.write(text.encode())


if __name__ == "__main__":
    test_error_numbers_are_valid_and_unique()
    test_error_codes_appear_in_correct_file()
    test_that_each_error_code_is_in_a_snippet()
