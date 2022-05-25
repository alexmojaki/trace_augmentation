import ast
import inspect
import sys
from collections import defaultdict
from functools import lru_cache

import stack_data
from cheap_repr import cheap_repr


@lru_cache()
def arg_names(co):
    args = inspect.getargs(co)
    result = args.args
    for name in [args.varargs, args.varkw]:
        if name is not None:
            result.append(name)
    return result


class Tracer:
    def __init__(self, filename):
        self.frames = {}
        self.filename = filename
        self.result = {}
        self.source = stack_data.Source.for_filename(filename)
        self.assignments_by_lineno = defaultdict(list)
        self.pieces_by_lineno = {}
        for piece in self.source.pieces:
            for lineno in piece:
                self.pieces_by_lineno[lineno] = piece
                for node in self.source._nodes_by_line[lineno]:
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                        self.assignments_by_lineno[lineno].append(node.id)

        self.last_piece = None

    def _trace(self, frame, event, arg):
        co = frame.f_code
        if co.co_filename != self.filename or co.co_name.startswith("<"):
            return
        qualname = self.source.code_qualname(co)
        if qualname not in self.result:
            lines, startline = inspect.getsourcelines(co)
            self.result[qualname] = dict(
                source=dict(
                    lines=lines,
                    startline=startline,
                ),
                calls=[],
            )
        func_info = self.result[qualname]
        if event == 'return':
            frame_info = self.frames.pop(frame)
            frame_info["return"] = arg
            func_info["calls"].append(frame_info)
        elif event == 'exception':
            del self.frames[frame]
        elif event == 'call':
            args = {
                k: cheap_repr(frame.f_locals[k])
                for k in arg_names(co)
            }
            self.frames[frame] = dict(args=args, lines=[], assignments=defaultdict(list))
            return self._trace
        elif event == 'line':
            startline = func_info["source"]["startline"]
            frame_info = self.frames[frame]
            frame_info["lines"].append(frame.f_lineno - startline)
            piece = self.pieces_by_lineno[frame.f_lineno]
            if self.last_piece not in (piece, None):
                for lineno in self.last_piece:
                    if assignments := self.assignments_by_lineno.get(lineno):
                        frame_info["assignments"][lineno - startline].append({
                            name: cheap_repr(frame.f_locals[name])
                            for name in assignments
                            if name in frame.f_locals
                        })
            self.last_piece = piece

            return self._trace

    def set_trace(self):
        sys.settrace(self._trace)


def annotated_lines(func_info, call):
    result = []
    for lineno, line in enumerate(func_info["source"]["lines"]):
        line = line.rstrip()
        if assignments := call["assignments"].get(lineno):
            label = ", ".join(f"{name} = {value}" for name, value in assignments[0].items())
            line += f"  # {label}"
        result.append(line)
    return result
