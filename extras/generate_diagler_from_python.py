
import sys
import re
from _ctypes import PyObj_FromPtr
import json
import ast
import tokenize
import intervaltree
import pathlib
import glob
from collections import defaultdict
from datetime import datetime


colors = [
    "#ff7c72", "#95ed7b", "#aa7ded", "#ef81c5", "#a5faff", "#92f78c",
    "#f2a6a2", "#7bf2ae", "#9ef7ee", "#83cfef", "#f796e0", "#6ff287", "#8eea69",
    "#90c9f4", "#f9b08b", "#b9fca9", "#ffc9e0", "#abef83", "#f3fca1",
    "#74f7e3", "#bd80f2", "#ff9ed6", "#6976db", "#e0c2fc", "#f2dd98", "#daed7d",
    "#f2a771", "#f4adc6", "#9a8cf2", "#fffcb2", "#dd88ea", "#f27c6d", "#f7e485",
    "#a1ff91", "#ffafe4", "#fce8b8", "#fcc7c9", "#76bef2", "#e080ed", "#f489d8",
    "#c8b2f4", "#f4e2a6", "#fcd3a4", "#9ff9bc", "#b0b0f4", "#d499ef", "#a5ebef",
    "#7cefbf", "#a3fc83", "#c7fc92", "#a8e7f7", "#f98bb9", "#b286ef", "#f9c7a7",
    "#88e0ef", "#fc83e8", "#91e7ea", "#c2e5f9", "#7e9bea", "#d5ffa5", "#d8fc7e",
    "#f26fbb", "#a6ef7c", "#d5f77e"
]
color_index = 0
topdir_colors = {}


# NoIndent & MyEncoder from: https://stackoverflow.com/a/13252112

class NoIndent(object):
    """ Value wrapper. """
    def __init__(self, value):
        self.value = value


class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))

    def __init__(self, **kwargs):
        # Save copy of any keyword argument values needed for use here.
        self.__sort_keys = kwargs.get('sort_keys', None)
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent)
                else super(MyEncoder, self).default(obj))

    def encode(self, obj):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.
        json_repr = super(MyEncoder, self).encode(obj)  # Default JSON.

        # Replace any marked-up object ids in the JSON repr with the
        # value returned from the json.dumps() of the corresponding
        # wrapped Python object.
        for match in self.regex.finditer(json_repr):
            # see https://stackoverflow.com/a/15012814/355230
            id = int(match.group(1))
            no_indent = PyObj_FromPtr(id)
            json_obj_repr = json.dumps(no_indent.value, sort_keys=self.__sort_keys)

            # Replace the matched id string with json formatted representation
            # of the corresponding Python object.
            json_repr = json_repr.replace(
                            '"{}"'.format(format_spec.format(id)), json_obj_repr)

        return json_repr


# ast things copied from here:
#   https://julien.danjou.info/finding-definitions-from-a-source-file-and-a-line-number-in-python/

def parse_file(filename):
    with tokenize.open(filename) as f:
        code = f.read()
        nodes = ast.parse(code, filename=filename)
        linetree = intervaltree.IntervalTree()
        for node in ast.walk(nodes):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start, end = compute_interval(node)
                linetree[start:end] = node

        return (nodes, linetree, code)


def compute_interval(node):
    min_lineno = node.lineno
    max_lineno = node.lineno
    for node in ast.walk(node):
        if hasattr(node, "lineno"):
            min_lineno = min(min_lineno, node.lineno)
            max_lineno = max(max_lineno, node.lineno)
    return (min_lineno, max_lineno+1)


def get_parent(linetree, lineno):
    matches = linetree[lineno]
    if matches:
        return min(matches, key=lambda i: i.length()).data.name


def get_parents(linetree, lineno):
    matches = linetree[lineno]
    lol = []
    for i in sorted(matches):
        lol.append(i.data.name)
    return lol


def create_decor_str(item, code):
    decors = []
    for dec in item.decorator_list:
        decors.append("@" + ast.get_source_segment(code, dec))
    decor_str = ""
    if len(decors):
        decor_str = f"{' '.join(decors)} "
    return decor_str


def extract_info(filename, import_path):
    file_info = {'imports': [], 'vars': [], 'methods': []}
    classes = {}

    (nodes, linetree, code) = parse_file(filename)

    for item in ast.walk(nodes):
        parents = []
        if hasattr(item, 'lineno'):
            parents = get_parents(linetree, item.lineno)

        if isinstance(item, (ast.Import, ast.ImportFrom)):
            names = []
            module = ""
            if hasattr(item, 'module'):
                if item.module:
                    module = f"{item.module}."
                else:
                    module = f"{import_path}."
            for alias in item.names:
                names.append(f"{module}{alias.name}")
            file_info['imports'].append({'names': names, 'str': ast.get_source_segment(code, item)})

        if isinstance(item, (ast.ClassDef)):
            bases = []
            for base in item.bases:
                bases.append(ast.get_source_segment(code, base))
            class_str = f"{create_decor_str(item, code)}class {item.name}({', '.join(bases)})"
            classes[item.name] = {'definition': class_str, 'methods': [], 'vars': []}

        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = []
            for arg in ast.walk(item.args):
                if isinstance(arg, ast.arg):
                    args.append(ast.get_source_segment(code, arg))
            ret = ""
            if item.returns:
                ret = " -> " + ast.get_source_segment(code, item.returns)
            def_str = f"{create_decor_str(item, code)}def {item.name}({', '.join(args)}){ret}"

            if len(parents) == 0:
                print(f"Warning: we have a method def without parents: {def_str}", file=sys.stderr)
            elif len(parents) == 1:
                file_info['methods'].append(def_str)
            elif len(parents) == 2:
                if parents[0] not in classes:
                    print(f"Warning: we have a method belonging to unknown class '{parents[0]}' - {def_str}",
                          file=sys.stderr)
                else:
                    classes[parents[0]]['methods'].append(def_str)
            else:
                print(f"Warning: we have a method def with deeeep hierargy {parents}: {def_str}", file=sys.stderr)

        if isinstance(item, (ast.Assign)):
            for target in item.targets:
                if len(parents) == 0:
                    file_info['vars'].append(ast.get_source_segment(code, target))
                if len(parents) == 1 and parents[0] in classes:
                    classes[parents[0]]['vars'].append(ast.get_source_segment(code, target))

        if isinstance(item, ast.AnnAssign):
            if len(parents) == 1:
                if parents[0] not in classes:
                    print(f"Warning: we have a method belonging to unknown class '{parents[0]}' - {def_str}",
                          file=sys.stderr)
                else:
                    classes[parents[0]]['vars'].append(ast.get_source_segment(code, item))

    return (file_info, classes)


importable = {}
all_classes = {}
extracted_infos = {}
script_dir = pathlib.Path(__file__).parent.absolute()
files = glob.glob(f"{script_dir}/../agw" + '/**/*.py', recursive=True)
for file_name in files:
    short_name = file_name.split('/../agw/')[1]
    import_path = short_name[0:-3].replace('/', '.')

    if import_path.endswith('.__init__'):
        import_path = import_path.replace('.__init__', '')
        (file_info, classes) = extract_info(file_name, import_path)
        for imp in file_info['imports']:
            for impname in imp['names']:
                k = f"{import_path}.{impname.split('.')[-1]}"
                v = f"{import_path}.{impname}"
                importable[k] = v

        continue

    (file_info, classes) = extract_info(file_name, import_path)

    for cname in classes.keys():
        impname = f"{import_path}.{cname}"
        all_classes[impname] = short_name

    extracted_infos[short_name] = {'import_path': import_path, 'file_info': file_info, 'classes': classes}

"""
print(json.dumps(extracted_infos, indent=4), file=sys.stderr)
print("IMPORTABLE:", file=sys.stderr)
print(json.dumps(importable, indent=4), file=sys.stderr)
print("ALL_CLASSES:", file=sys.stderr)
print(json.dumps(all_classes, indent=4), file=sys.stderr)
"""

output = {
    "__STYLE__": {
        "class": {
            "background-color": "#DDF"
        },
        "global": {
            "background-color": "#DFD"
        },
        "__EDGE__": {
            "width": 2,
            "arrow-scale": 4,
            "line-color": "#555",
            "color": "#F99",
            "font-size": "80px",
            "text-outline-width": 4,
            # "GROUP-EDGE-TARGETS-PERCENTAGE": 0.25,
            # "GROUP-EDGE-SOURCES-PERCENTAGE": 0.30
        }
    },
    "header": [
        {
            "object": "style",
            "label": f"AGW Architecture ({datetime.now().strftime('%Y%m%d_%H%M')})",
            "font-size": "65px",
            "width": 3,
            "height": 3
        }
    ]
}

seen_imports = defaultdict(dict)
for short_name, info in extracted_infos.items():
    top_dir = short_name.split('/')[0]
    bgcolor = "#DDD"
    dir_container = None
    if top_dir != short_name:
        if top_dir not in topdir_colors:
            topdir_colors[top_dir] = colors[color_index]
            color_index += 1
        bgcolor = topdir_colors[top_dir]
        dir_container = top_dir
        if dir_container not in output:
            output[dir_container] = {
                "__CONTAINERINFO__": [
                    NoIndent({"object": "style", "background-color": bgcolor, "font-size": "40px"})
                ]
            }

    module_name = f'{short_name}.module'
    f = {
        "__CONTAINERINFO__": [
            NoIndent({"object": "style", "background-color": "#CCF", "font-size": "30px"})
        ],
        f"{module_name}": [NoIndent({"object": "style", "type": "global", "label": ""})]
    }

    if len(info['file_info']['imports']) > 0:
        f[f"{module_name}"].append(NoIndent({"object": "separator", "label": "Imports"}))
        for imp in info['file_info']['imports']:
            f[f"{module_name}"].append(NoIndent([imp['str']]))
            for impname in imp['names']:
                if impname in all_classes or (impname in importable and importable[impname] in all_classes):
                    if impname in importable:
                        to = all_classes[importable[impname]]
                    else:
                        to = all_classes[impname]
                    if to not in seen_imports[short_name]:
                        f["__CONTAINERINFO__"].append(NoIndent({"object": "reference", "to": to}))
                    seen_imports[short_name][to] = 1
                else:
                    print(f"Not an importable: {impname}", file=sys.stderr)

    if len(info['file_info']['vars']) > 0:
        f[f"{module_name}"].append(NoIndent({"object": "separator", "label": "Module Variables"}))
        for v in info['file_info']['vars']:
            f[f"{module_name}"].append(NoIndent([v]))

    if len(info['file_info']['methods']) > 0:
        f[f"{module_name}"].append(NoIndent({"object": "separator", "label": "Module Methods"}))
        for m in info['file_info']['methods']:
            f[f"{module_name}"].append(NoIndent([m]))

    for cname, cinfo in info['classes'].items():
        impname = f"{info['import_path']}.{cname}"
        f[impname] = [NoIndent({"object": "style", "type": "class", "label": cinfo['definition']})]
        if len(cinfo['vars']) > 0:
            f[impname].append(NoIndent({"object": "separator", "label": "Class Variables"}))
            for v in cinfo['vars']:
                f[impname].append(NoIndent([v]))
        if len(cinfo['methods']) > 0:
            f[impname].append(NoIndent({"object": "separator", "label": "Methods"}))
            for m in cinfo['methods']:
                f[impname].append(NoIndent([m]))

    s = short_name
    if s in importable:
        s = importable[s]
    if dir_container:
        output[dir_container][s] = f
    else:
        output[s] = f

print(json.dumps(output, indent=4, cls=MyEncoder))
