import glob
import html.parser
import io
import os
import pprint
import re
import shutil
import string
import sys
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set, Tuple

import sphinx

print("=============")
print(sphinx.__version__)
print("=============")
import sphinx.cmd.build

WARNING = "\033[93mWARNING"
ERROR = "\033[91mERROR"
END_COLOR = "\033[0m"

tokens = ["--internal", "--external", "--tracking"]
args_sanitized = []
build_options = []
targets_specified = []
is_target = False
is_home = False
home_url = ""
for arg in sys.argv[1:]:
    if is_target:
        targets_specified.append(arg)
        is_target = False
    elif arg == "--target":
        is_target = True
    elif arg == "--home":
        is_home = True
    elif is_home:
        home_url = arg
        is_home = False
    elif arg in tokens:
        build_options.append(arg)
    else:
        args_sanitized.append(arg)

bin_path = os.path.dirname(os.path.realpath(__file__))


def is_rst_file(file_path: str) -> bool:
    if file_path.endswith(".rst"):
        return True
    return False


def find_files(root_path: str, include_file: Callable[[str], bool]) -> List[str]:
    results = []
    for root, dirs, files in os.walk(root_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if include_file(file_path):
                results.append(file_path)
    return results


def find_files_above_size_limit(root_path: str) -> List[str]:
    def is_above_size_limit(file_path: str) -> bool:
        if os.path.getsize(file_path) > 1024 * 1024 * 100:
            return True
        return False

    return find_files(root_path, is_above_size_limit)


def generate_license_wrapper(doc_root_path: str, license_folder_path_relative: str, license_wrapper_path: str):
    print(f"Generating {license_wrapper_path} ...")
    license_folder_posix = license_folder_path_rel.replace("\\", "/")
    with open(license_wrapper_path, "w") as out:
        out.write(".. highlight:: none\n\n")
        license_folder_path = os.path.join(doc_root_path, license_folder_path_relative)
        for filename in os.listdir(license_folder_path):
            ix = filename.rfind("-")
            if ix == -1:
                raise RuntimeError(f"Filename '{filename}' is not a valid license file name.")

            package_name = filename[:ix]
            file_type = os.path.splitext(filename[ix + 1 :])[0].title()
            header = package_name + " " + file_type + "\n"
            out.write(header)
            out.write("-" * len(header) + "\n\n")
            out.write(f".. include:: {license_folder_posix}/{filename}\n")
            out.write("    :literal:\n\n")


def remove_string_from_files(key: str, file_paths: List[str]):
    for file_path in file_paths:
        with io.open(file_path, "r", encoding="utf8") as input_file:
            in_data = input_file.read()
        out_data = in_data.replace(key, "")
        with io.open(file_path, "w", encoding="utf8") as out_file:
            print("Stripped '%s' from '%s'" % (key, file_path))
            out_file.write(out_data)


def remove_self_from_files(file_paths: Iterable[str]):
    pattern1 = re.compile(r"<em>self: [\w.]+</em>[,]?[ ]*")
    pattern2 = re.compile(r"self: [\w.]+[,]?[ ]*")
    for file_path in file_paths:
        with io.open(file_path, "r", encoding="utf8") as input_file:
            in_data = input_file.read()
        out_data = pattern1.sub("", in_data)
        out_data = pattern2.sub("", out_data)
        with io.open(file_path, "w", encoding="utf8") as out_file:
            print("Removed self arguments from '%s'" % file_path)
            out_file.write(out_data)


def build_documentation(
    language: str,
    config_dir: str,
    input_dir: str,
    output_dir: str,
    additional_args: Optional[List[str]] = None,
    fail_on_warnings=True,
):
    print(f"\n*** Building {language} manual ({output_dir}) ***")
    args = ["-c", config_dir, "-j", "auto", "-b", "html", input_dir, output_dir]
    if fail_on_warnings:
        args.insert(0, "-W")

    # add system arguments
    args.extend(args_sanitized)
    if additional_args:
        args.extend(additional_args)

    exit_code = sphinx.cmd.build.main(args)

    if exit_code:
        print(f"{ERROR}: Error while building {language} manual !!!{END_COLOR}")
        sys.exit(exit_code)


def error(message: str, exit_code: int = 1):
    print(f"{ERROR}: {message}{END_COLOR}")
    sys.exit(1)


class HtmlParser(html.parser.HTMLParser):
    redirect_path = None

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        is_refresh = False
        content = None
        for key, value in attrs:
            if key == "http-equiv":
                if value.lower() == "refresh":
                    is_refresh = True
            if key == "content":
                content = value
        if is_refresh:
            _, url = content.split("=", 1)
            if url.startswith("/"):
                rel_path = "." + url
            else:
                rel_path = url
            ix = rel_path.find("#")
            if ix != -1:
                rel_path = rel_path[:ix]
            self.redirect_path = rel_path


def verify_redirect(path: str):
    parser = HtmlParser()
    with open(path, "r", encoding="utf8") as infile:
        data = infile.read()
    parser.feed(data)
    if parser.redirect_path and not parser.redirect_path.startswith("https://"):
        target_path = os.path.normpath(os.path.join(os.path.dirname(path), parser.redirect_path))
        if not os.path.exists(target_path):
            error(f"Redirect target '{parser.redirect_path}' resolves to path '{target_path}' which does not exist.")


def verify_redirects(path_list: List[Tuple[str, str]]):
    for input_path, output_path in path_list:
        if output_path.endswith(".html"):
            print(f"Verifying '{input_path}'...")
            verify_redirect(output_path)


def copy_redirects(input_dir: str, output_dir: str, files_copied: List[Tuple[str, str]]):
    names = os.listdir(input_dir)
    for name in names:
        input_fullname = os.path.join(input_dir, name)
        output_fullname = os.path.join(output_dir, name)
        if os.path.isdir(input_fullname):
            if not os.path.exists(output_fullname):
                os.mkdir(output_fullname)
            copy_redirects(input_fullname, output_fullname, files_copied)
        else:
            shutil.copyfile(input_fullname, output_fullname)
            files_copied.append((input_fullname, output_fullname))


def resolve_include_path(include_path: str, host_dir: str, top_dir: str) -> str:
    base, ext = os.path.splitext(include_path)
    if not ext:
        include_path += ".rst"
    if include_path.startswith("/"):
        include_path = "." + include_path
        norm = os.path.join(top_dir, include_path)
    else:
        norm = os.path.join(host_dir, include_path)
    norm = os.path.normpath(norm)
    return norm


def resolve_toc_path(toc_path: str, host_dir: str, top_dir: str) -> str:
    if toc_path.startswith("http://") or toc_path.startswith("https://"):
        return toc_path
    base, ext = os.path.splitext(toc_path)
    if not ext:
        toc_path += ".rst"
    if toc_path.startswith("/"):
        toc_path = "." + toc_path
        toc_path = os.path.join(top_dir, toc_path)
    else:
        toc_path = os.path.join(host_dir, toc_path)
    toc_path = os.path.normpath(toc_path)
    return toc_path


def resolve_toc_glob(pattern: str, host_dir: str, top_dir: str) -> List[str]:
    abs_pattern = resolve_toc_path(pattern, host_dir, top_dir)
    paths = glob.glob(abs_pattern, recursive=True)
    return paths


def extract_referenced_paths(file_path: str, host_dir: str, top_dir: str, toc_refs: Set[str], inc_refs: Set[str]):
    include = ".. include::"
    include_len = len(include)
    doc = ":doc:`"
    doc_len = len(doc)
    toc = ".. toctree::"
    print(f"Loading referenced file from `{file_path}`")
    with open(file_path, encoding="utf-8") as infile:
        is_toc = False
        while True:
            is_include = False
            path = None
            path_host_dir = host_dir
            line = infile.readline()
            if not line:
                break
            ix = line.find(include)
            if ix != -1:
                path = line[ix + include_len :].split()[0]
                path = path.strip()
                path = resolve_include_path(path, host_dir, top_dir)
                is_include = True
            ix = line.find(doc)
            if ix != -1:
                path = line[ix + doc_len :].split("`")[0]
                ix = path.find("<")
                if ix != -1:
                    end_ix = path.find(">", ix)
                    if end_ix != -1:
                        path = path[ix + 1 : end_ix]
                path = resolve_include_path(path, path_host_dir, top_dir)
                path_host_dir = os.path.dirname(path)
            ix = line.find(toc)
            if ix != -1:
                is_toc = True
                continue
            if is_toc and not is_include:
                toc_setting = line.startswith("   ") or line.startswith("\n")
                if toc_setting == False:
                    is_toc = False
                    continue
                command = line.strip()
                if command and not command.startswith(":"):
                    ix = command.find("<")
                    if ix != -1:
                        end_ix = command.find(">", ix)
                        if end_ix != -1:
                            command = command[ix + 1 : end_ix]
                    if "*" in command:
                        path_list = resolve_toc_glob(command, host_dir, top_dir)
                        for p in path_list:
                            if p in toc_refs:
                                continue
                            toc_refs.add(p)
                            path_host_dir = os.path.dirname(p)
                            extract_referenced_paths(p, path_host_dir, top_dir, toc_refs, inc_refs)
                    else:
                        path = resolve_toc_path(command, host_dir, top_dir)
                        path_host_dir = os.path.dirname(path)

            if path:
                if path.startswith("http://") or path.startswith("https://"):
                    toc_refs.add(path)
                    continue
                if not os.path.exists(path):
                    # Note that this check is not needed above in the glob case
                    print(f"{ERROR}: File '{file_path}' refers to path '{path}' which doesn't exist!{END_COLOR}")
                    sys.exit(1)
                if is_include:
                    if path in inc_refs:
                        continue
                    inc_refs.add(path)
                else:
                    if path in toc_refs:
                        continue
                    toc_refs.add(path)
                extract_referenced_paths(path, path_host_dir, top_dir, toc_refs, inc_refs)


def create_exclusion_list(all_rst, included_rst):
    excluded_rst = []
    for rst in all_rst:
        if not rst in included_rst:
            excluded_rst.append(rst)
    return excluded_rst


def make_paths_sphinx_conformant(paths, base):
    bundled_paths = []
    rel = []

    # by determining groups of paths that can be replaced with wildcards, build can speed up 2-3x
    # but have to be careful not to replace paths where a wildcard would exclude a file being used
    # if we had wcmatch this could act recursively with less code but this is good enough
    for parent in list({os.path.dirname(_parent_path) for _parent_path in paths}):
        exts = list({Path(f).suffix for f in os.listdir(parent) if "." in f})
        # exts = [".rst", ".md", ".txt"]
        for ext in exts:
            sublisting = [
                _name
                for _name in os.listdir(parent)
                if _name.endswith(ext) and os.path.isfile(os.path.join(parent, _name))
            ]
            all_in = True
            for sub in sublisting:
                subpath = os.path.join(parent, sub)
                if subpath in paths:
                    continue
                else:
                    all_in = False
            if all_in:
                uses_ext = any(sub.endswith(ext) for sub in sublisting)
                if uses_ext:
                    bundled_paths.append(os.path.join(parent, f"*{ext}"))
            else:
                fallback_paths = [path for path in paths if Path(path).match(f"{parent}{os.path.sep}*{ext}")]
                for path in fallback_paths:
                    bundled_paths.append(path)

    for path in bundled_paths:
        path_rel = os.path.relpath(path, base)
        path_rel = path_rel.replace(os.path.sep, "/")
        rel.append(path_rel)

    # doesn't need to be sorted but it's easier to human-read in the conf.py
    return sorted(rel)


def customize_conf(master_doc_path, custom_path, exclusion_list, conf_path):
    source_dir = os.path.dirname(master_doc_path)
    exclude_rel = make_paths_sphinx_conformant(exclusion_list, source_dir)
    master_doc_name = os.path.basename(master_doc_path)
    master_doc_name, ext = os.path.splitext(master_doc_name)
    with open(custom_path, encoding="utf8") as infile:
        custom_data = infile.read()
    with open(conf_path, "a", encoding="utf8") as outfile:
        outfile.write(f"{custom_data}\n")
        outfile.write(f"master_doc = '{master_doc_name}'\n")
        outfile.write("exclude_patterns = ")
        pprint.pprint(exclude_rel, stream=outfile)


def update_layout_file(file_path, home_url, doc_pre, doc_post):
    with open(file_path, "rt", encoding="utf8") as infile:
        text = infile.read()
    template = string.Template(text)
    tokens = {"home_url": home_url, "doc_pre": doc_pre, "doc_post": doc_post}
    out = template.substitute(tokens)
    with open(file_path, "wt", encoding="utf8") as outfile:
        outfile.write(out)


def update_breadcrumbs_file(file_path, home_url):
    with open(file_path, "rt", encoding="utf8") as infile:
        text = infile.read()
    template = string.Template(text)
    tokens = {"home_url": home_url}
    out = template.substitute(tokens)
    with open(file_path, "wt", encoding="utf8") as outfile:
        outfile.write(out)


def generate_configuration(
    master_doc_path: str, default_conf_dir: str, custom_path: str, all_rst: List[str], output_dir: str
) -> List[str]:
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    shutil.copytree(default_conf_dir, output_dir)
    layout_file_path = os.path.join(output_dir, "templates", "layout.html")
    breadcrumbs_file_path = os.path.join(output_dir, "templates", "breadcrumbs.html")
    if "--tracking" in build_options:
        doc_pre = R"""<!-- Adobe tracking script -->
            <script src="//assets.adobedtm.com/b92787824f2e0e9b68dc2e993f9bd995339fe417/satelliteLib-07d828cd547199f009a1a2e885a826d41f4909b5.js" >
            </script>"""
        doc_post = R"""<!-- Invoking Adobe tracking -->
            <script type="text/javascript">_satellite.pageBottom();</script>"""
    else:
        doc_pre = doc_post = ""
    update_layout_file(layout_file_path, home_url, doc_pre, doc_post)
    update_breadcrumbs_file(breadcrumbs_file_path, home_url)
    host_dir = top_dir = os.path.dirname(master_doc_path)
    toc_refs = set()
    inc_refs = set()
    extract_referenced_paths(master_doc_path, host_dir, top_dir, toc_refs, inc_refs)
    toc_refs.add(master_doc_path)
    exclude = create_exclusion_list(all_rst, toc_refs)
    conf_path = os.path.join(output_dir, "conf.py")
    customize_conf(master_doc_path, custom_path, exclude, conf_path)
    refs = toc_refs | inc_refs
    return refs


def is_sphinx_file(file_path):
    if file_path.endswith(".rst") or file_path.endswith(".md"):
        return True
    return False


build_prefixes = [
    "prod_",
    "app_",
    "exp_",
    "con_",
    "plat_",
]


def find_build_targets(source_dir: str) -> List[str]:
    targets = []
    file_names = os.listdir(source_dir)
    for file_name in file_names:
        if file_name.endswith(".rst"):
            for prefix in build_prefixes:
                if file_name.startswith(prefix):
                    targets.append(file_name[: len(file_name) - 4])
                    break
    return targets


def copy_css_files(source_dir: str, target_dir: str):
    for item in os.listdir(source_dir):
        if item.endswith(".css"):
            shutil.copyfile(os.path.join(source_dir, item), os.path.join(target_dir, item))


repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

source_dir = os.path.join(repo_dir, "docs")
targets = find_build_targets(source_dir)
if targets_specified:
    for i in targets_specified:
        if i not in targets:
            print(f"{ERROR} Target '{i}' is not valid!{END_COLOR}")
            print(f"Valid targets are: {targets}")
            sys.exit(1)
    targets = targets_specified

# find all .rst/.md files:
all_rst = find_files(source_dir, is_sphinx_file)

build_root_dir = os.path.join(repo_dir, "_build")
target_conf_root_dir = os.path.join(build_root_dir, "conf")

license_folder_path_rel = "license_files"
common_dir = os.path.join(source_dir, "common")
license_wrapper_path = os.path.join(common_dir, "license_wrapper.tmp")
generate_license_wrapper(common_dir, license_folder_path_rel, license_wrapper_path)

index_paths = []
included_files = set()

for target_name in targets:
    target_conf_dir = os.path.join(target_conf_root_dir, target_name)
    source_conf_dir = os.path.join(source_dir, "conf")
    source_master = os.path.join(source_dir, target_name) + ".rst"
    custom_path = os.path.join(source_dir, target_name, "custom.py")
    referenced_files = generate_configuration(source_master, source_conf_dir, custom_path, all_rst, target_conf_dir)
    included_files.update(set(referenced_files))

    if "--internal" in build_options:
        build_dir = os.path.join(repo_dir, "_build", "internal", target_name)
        build_documentation(f"{target_name} - Internal", target_conf_dir, source_dir, build_dir, ["-t", "internal"])
        copy_css_files(os.path.join(source_conf_dir), os.path.join(build_dir, "_static"))
        index_path = os.path.join(build_dir, target_name + ".html")
        index_paths.append(index_path)

    if "--external" in build_options:
        build_dir = os.path.join(repo_dir, "_build", "external", target_name)
        build_documentation(f"{target_name} - External", target_conf_dir, source_dir, build_dir)
        copy_css_files(os.path.join(source_conf_dir), os.path.join(build_dir, "_static"))
        index_path = os.path.join(build_dir, target_name + ".html")
        index_paths.append(index_path)

if "--internal" in build_options:
    paths = []
    copy_redirects(os.path.join(repo_dir, "redirects"), os.path.join(repo_dir, "_build", "internal"), paths)
    if not targets_specified:  # we cannot verify redirects if only some targets are being built
        verify_redirects(paths)

if "--external" in build_options:
    paths = []
    copy_redirects(os.path.join(repo_dir, "redirects"), os.path.join(repo_dir, "_build", "external"), paths)
    if not targets_specified:  # we cannot verify redirects if only some targets are being built
        verify_redirects(paths)


if len(included_files) != len(all_rst):
    print(f"\n{WARNING}: Found the following orphaned files (not referenced anywhere via toc or include)")
    intersection = set(all_rst) - included_files
    for i in intersection:
        print(i)
    sys.stdout.write(END_COLOR)

res = find_files_above_size_limit(os.path.join(repo_dir, "_build", "external"))
if res:
    print(f"{ERROR}: Found files above the size limit of 100 MB for website publishing:")
    for file_path in res:
        print(file_path)
    print(f"Reduce *source* file size or host these files externally.{END_COLOR}")
    sys.exit(1)

print("\nList of root HTML pages produced:")
for path in index_paths:
    print(path)
