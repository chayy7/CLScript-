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
                # Try to parse as int or float
                try:
                    if '.' in val:
                        inputs[var] = float(val)
                    else:
                        inputs[var] = int(val)
                except ValueError:
                    inputs[var] = val  # fallback as string if needed

    output = ""

    # Helper to evaluate expressions safely in variables context
    def eval_expr(expr):
        try:
            return eval(expr, {}, variables)
        except Exception as e:
            raise Exception(f"Error evaluating expression '{expr}': {e}")

    # Helper to get a block of code lines indented under the current line
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

    # Helper to parse if-elif-else blocks without needing 'end'
    def parse_if_block(start_index):
        blocks = []  # List of tuples (type, condition, block_lines)
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

    # Helper to parse switch-case blocks without 'end'
    def parse_switch_block(start_index):
        cases = []  # List of tuples (case_value, block_lines), case_value can be None for default
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
        indent = len(lines[i]) - len(raw_line.lstrip())

        if line.startswith("keep "):
            try:
                var, value = line[5:].split('=')
                var = var.strip()
                value = value.strip()
                variables[var] = eval_expr(value)
            except Exception as e:
                output += f"Error in keep: {e}\n"
            i += 1

        elif line.startswith("input int "):
            var = line[10:].strip()
            if var in inputs:
                try:
                    variables[var] = int(inputs[var])
                except ValueError:
                    output += f"Invalid int input for {var}\n"
            else:
                output += f"Missing input for {var}\n"
            i += 1

        elif line.startswith("input float "):
            var = line[12:].strip()
            if var in inputs:
                try:
                    variables[var] = float(inputs[var])
                except ValueError:
                    output += f"Invalid float input for {var}\n"
            else:
                output += f"Missing input for {var}\n"
            i += 1

        elif line.startswith("output "):
            expr = line[7:].strip()
            try:
                result = eval_expr(expr)
                output += str(result) + "\n"
            except Exception as e:
                output += f"Error in output: {e}\n"
            i += 1

        # IF-ELIF-ELSE
        elif line.startswith("if "):
            blocks, next_i = parse_if_block(i)
            executed = False
            for btype, cond, block_lines in blocks:
                if btype == "else":
                    # Execute else block if no prior condition matched
                    if not executed:
                        output += interpret_cscript("\n".join(line.lstrip() for line in block_lines), "")
                        executed = True
                else:
                    try:
                        if eval_expr(cond):
                            output += interpret_cscript("\n".join(line.lstrip() for line in block_lines), "")
                            executed = True
                    except Exception as e:
                        output += f"Error in if condition '{cond}': {e}\n"
                if executed:
                    break
            i = next_i

        # SWITCH CASE
        elif line.startswith("switch "):
            switch_expr = line[7:].strip()
            i += 1
            cases, next_i = parse_switch_block(i)
            try:
                switch_val = eval_expr(switch_expr)
                executed_case = False
                for case_val, block_lines in cases:
                    if case_val is not None:
                        try:
                            case_eval = eval_expr(case_val)
                        except:
                            case_eval = case_val  # fallback string
                        if switch_val == case_eval:
                            output += interpret_cscript("\n".join(line.lstrip() for line in block_lines), "")
                            executed_case = True
                            break
                    else:
                        # default case
                        if not executed_case:
                            output += interpret_cscript("\n".join(line.lstrip() for line in block_lines), "")
                            executed_case = True
                            break
            except Exception as e:
                output += f"Error in switch expression '{switch_expr}': {e}\n"
            i = next_i

        # WHILE loop
        elif line.startswith("while "):
            cond_expr = line[6:].strip()
            i += 1
            if i < len(lines):
                body_indent = len(lines[i]) - len(lines[i].lstrip())
                body_lines, next_pos = get_block(i, body_indent)
            else:
                body_lines = []
                next_pos = i

            try:
                while eval_expr(cond_expr):
                    output += interpret_cscript("\n".join(line.lstrip() for line in body_lines), "")
            except Exception as e:
                output += f"Error in while loop condition '{cond_expr}': {e}\n"

            i = next_pos

        # DO WHILE loop
        elif line.startswith("do while "):
            cond_expr = line[9:].strip()
            i += 1
            if i < len(lines):
                body_indent = len(lines[i]) - len(lines[i].lstrip())
                body_lines, next_pos = get_block(i, body_indent)
            else:
                body_lines = []
                next_pos = i

            try:
                while True:
                    output += interpret_cscript("\n".join(line.lstrip() for line in body_lines), "")
                    if not eval_expr(cond_expr):
                        break
            except Exception as e:
                output += f"Error in do while loop condition '{cond_expr}': {e}\n"

            i = next_pos

        # FOR loop (C-style for(init; cond; incr))
        elif line.startswith("for "):
            for_content = line[4:].strip()
            try:
                init_part, cond_part, incr_part = [x.strip() for x in for_content.split(';')]
            except Exception:
                output += "Invalid for loop syntax. Use: for init; condition; increment\n"
                i += 1
                continue

            try:
                exec(init_part, {}, variables)
            except Exception as e:
                output += f"Error in for-loop init '{init_part}': {e}\n"
                i += 1
                continue

            i += 1
            if i < len(lines):
                body_indent = len(lines[i]) - len(lines[i].lstrip())
                body_lines, next_pos = get_block(i, body_indent)
            else:
                body_lines = []
                next_pos = i

            try:
                while eval_expr(cond_part):
                    output += interpret_cscript("\n".join(line.lstrip() for line in body_lines), "")
                    exec(incr_part, {}, variables)
            except Exception as e:
                output += f"Error in for-loop condition/increment: {e}\n"

            i = next_pos

        # FOR EACH loop
        elif line.startswith("for each "):
            for_each_content = line[9:].strip()
            if ' in ' not in for_each_content:
                output += "Invalid for each syntax. Use: for each var in collection\n"
                i += 1
                continue

            var_name, collection_name = [x.strip() for x in for_each_content.split(' in ', 1)]
            collection = variables.get(collection_name, None)
            if collection is None:
                output += f"Collection '{collection_name}' not found for for each loop.\n"
                i += 1
                continue

            if not hasattr(collection, '__iter__'):
                output += f"Variable '{collection_name}' is not iterable.\n"
                i += 1
                continue

            i += 1
            if i < len(lines):
                body_indent = len(lines[i]) - len(lines[i].lstrip())
                body_lines, next_pos = get_block(i, body_indent)
            else:
                body_lines = []
                next_pos = i

            for item in collection:
                variables[var_name] = item
                output += interpret_cscript("\n".join(line.lstrip() for line in body_lines), "")

            i = next_pos

        else:
            # Unknown or empty line - just skip
            i += 1

    return output
