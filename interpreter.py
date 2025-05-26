variables = {}

def interpret_cscript(code, input_string=""):
    lines = code.strip('\n').split('\n')
    inputs = {}

    if input_string:
        for part in input_string.split(','):
            if '=' in part:
                var, val = part.strip().split('=')
                var = var.strip()
                val = val.strip()
                try:
                    if '.' in val:
                        inputs[var] = float(val)
                    else:
                        inputs[var] = int(val)
                except ValueError:
                    try:
                        inputs[var] = eval(val)
                    except:
                        inputs[var] = val

    output = ""

    def eval_expr(expr):
        try:
            return eval(expr, {}, variables)
        except Exception as e:
            raise Exception(f"Error evaluating expression '{expr}': {e}")

    def get_block(start_index, start_indent):
        block_lines = []
        i = start_index
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if stripped == "" or indent < start_indent:
                break
            block_lines.append(line)
            i += 1
        return block_lines, i

    def parse_if_block(start_index):
        blocks = []
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("if "):
                cond = line[3:].strip()
                i += 1
                block_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
                block_lines, i = get_block(i, block_indent)
                blocks.append(("if", cond, block_lines))
            elif line.startswith("elif "):
                cond = line[5:].strip()
                i += 1
                block_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
                block_lines, i = get_block(i, block_indent)
                blocks.append(("elif", cond, block_lines))
            elif line == "else":
                i += 1
                block_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
                block_lines, i = get_block(i, block_indent)
                blocks.append(("else", None, block_lines))
                break
            else:
                break
        return blocks, i

    def parse_switch_block(start_index):
        cases = []
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("case "):
                case_val = line[5:].strip()
                i += 1
                block_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
                block_lines, i = get_block(i, block_indent)
                cases.append((case_val, block_lines))
            elif line == "default":
                i += 1
                block_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
                block_lines, i = get_block(i, block_indent)
                cases.append((None, block_lines))
                break
            else:
                break
        return cases, i

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        raw_line = lines[i]
        indent = len(raw_line) - len(raw_line.lstrip())

        if line.startswith("inp "):
            try:
                var, value = line[4:].split('=')
                variables[var.strip()] = eval_expr(value.strip())
            except Exception as e:
                output += f"Error in inp: {e}\n"
            i += 1

        elif line.startswith("input int "):
            var = line[10:].strip()
            variables[var] = int(inputs.get(var, 0))
            i += 1

        elif line.startswith("input float "):
            var = line[12:].strip()
            variables[var] = float(inputs.get(var, 0.0))
            i += 1

        elif line.startswith("out "):
            expr = line[4:].strip()
            try:
                result = eval_expr(expr)
                output += str(result) + "\n"
            except Exception as e:
                output += f"Error in out: {e}\n"
            i += 1

        elif line.startswith("if "):
            blocks, next_i = parse_if_block(i)
            executed = False
            for btype, cond, block_lines in blocks:
                if btype == "else":
                    if not executed:
                        output += interpret_cscript("\n".join(l.lstrip() for l in block_lines), "")
                        executed = True
                else:
                    try:
                        if eval_expr(cond):
                            output += interpret_cscript("\n".join(l.lstrip() for l in block_lines), "")
                            executed = True
                    except Exception as e:
                        output += f"Error in {btype} condition '{cond}': {e}\n"
                if executed:
                    break
            i = next_i

        elif line.startswith("switch "):
            switch_expr = line[7:].strip()
            i += 1
            cases, next_i = parse_switch_block(i)
            try:
                switch_val = eval_expr(switch_expr)
                executed_case = False
                for case_val, block_lines in cases:
                    try:
                        if case_val is not None and eval_expr(case_val) == switch_val:
                            output += interpret_cscript("\n".join(l.lstrip() for l in block_lines), "")
                            executed_case = True
                            break
                    except:
                        continue
                if not executed_case:
                    for case_val, block_lines in cases:
                        if case_val is None:
                            output += interpret_cscript("\n".join(l.lstrip() for l in block_lines), "")
                            break
            except Exception as e:
                output += f"Error in switch expression '{switch_expr}': {e}\n"
            i = next_i

        elif line.startswith("while "):
            cond_expr = line[6:].strip()
            i += 1
            body_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
            body_lines, next_i = get_block(i, body_indent)
            try:
                while eval_expr(cond_expr):
                    output += interpret_cscript("\n".join(l.lstrip() for l in body_lines), "")
            except Exception as e:
                output += f"Error in while loop: {e}\n"
            i = next_i

        elif line.startswith("do while "):
            cond_expr = line[9:].strip()
            i += 1
            body_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
            body_lines, next_i = get_block(i, body_indent)
            try:
                while True:
                    output += interpret_cscript("\n".join(l.lstrip() for l in body_lines), "")
                    if not eval_expr(cond_expr):
                        break
            except Exception as e:
                output += f"Error in do while loop: {e}\n"
            i = next_i

        elif line.startswith("for each "):
            content = line[9:].strip()
            if ' in ' not in content:
                output += "Invalid for each syntax.\n"
                i += 1
                continue
            var_name, collection_name = map(str.strip, content.split(' in ', 1))
            collection = variables.get(collection_name, [])
            if not hasattr(collection, '__iter__'):
                output += f"Variable '{collection_name}' is not iterable.\n"
                i += 1
                continue
            i += 1
            body_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
            body_lines, next_i = get_block(i, body_indent)
            for item in collection:
                variables[var_name] = item
                output += interpret_cscript("\n".join(l.lstrip() for l in body_lines), "")
            i = next_i

        elif line.startswith("for ") and "to" in line:
            try:
                left, right = line[4:].split("to")
                var, start_val = left.split('=')
                var = var.strip()
                start_val = eval_expr(start_val.strip())
                end_val = eval_expr(right.strip())
                i += 1
                body_indent = len(lines[i]) - len(lines[i].lstrip()) if i < len(lines) else 0
                body_lines, next_i = get_block(i, body_indent)
                for loop_val in range(start_val, end_val):
                    variables[var] = loop_val
                    output += interpret_cscript("\n".join(l.lstrip() for l in body_lines), "")
                i = next_i
            except Exception as e:
                output += f"Invalid for loop syntax: {e}\n"
                i += 1

        else:
            i += 1

    return output
