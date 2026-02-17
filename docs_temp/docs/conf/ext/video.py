import os

import sphinx
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.osutil import copyfile


def get_option(options, key, default):
    if key not in options.keys():
        return default

    if type(default) == type(True):
        return True
    else:
        return options[key]


class video(nodes.General, nodes.Element):
    pass


class Video(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 11
    final_argument_whitespace = False
    option_spec = {
        "type": directives.unchanged,
        "alt": directives.unchanged,
        "width": directives.unchanged,
        "height": directives.unchanged,
        "autoplay": directives.flag,
        "nocontrols": directives.flag,
        "loop": directives.flag,
        "onplay": directives.unchanged,
        "playsinline": directives.flag,
        "muted": directives.flag,
        "centered": directives.flag,
    }

    def is_remote(self, uri):
        uri = uri.strip()
        env = self.state.document.settings.env
        app_directory = os.path.dirname(os.path.abspath(self.state.document.settings._source))
        if sphinx.__version__.startswith("1.1"):
            app_directory = app_directory.decode("utf-8")

        if uri[0] == "/":
            return False
        if uri[0:7] == "file://":
            return False
        if os.path.isfile(os.path.join(env.srcdir, uri)):
            return False
        if os.path.isfile(os.path.join(app_directory, uri)):
            return False
        if "://" in uri:
            return True
        raise ValueError(
            "Video URI `{}` have to be local relative or " "absolute path to video, or remote address.".format(uri)
        )

    def run(self):
        _type = get_option(self.options, "type", "mp4")
        alt = get_option(self.options, "alt", "Video")
        width = get_option(self.options, "width", "")
        height = get_option(self.options, "height", "")
        autoplay = get_option(self.options, "autoplay", False)
        nocontrols = get_option(self.options, "nocontrols", False)
        loop = get_option(self.options, "loop", False)
        onplay = get_option(self.options, "onplay", "")
        playsinline = get_option(self.options, "playsinline", False)
        muted = get_option(self.options, "muted", False)
        path = self.arguments[0]
        remote = self.is_remote(path)
        centered = get_option(self.options, "centered", False)

        return [
            video(
                path=self.arguments[0],
                alt=alt,
                width=width,
                height=height,
                autoplay=autoplay,
                nocontrols=nocontrols,
                loop=loop,
                onplay=onplay,
                _type=_type,
                playsinline=playsinline,
                muted=muted,
                remote=remote,
                centered=centered,
            )
        ]


def visit_video_node(self, node):

    path = node["path"]
    youtube_source = False
    if node["remote"]:
        youtube_source = "youtube" in path or "youtu.be" in path
        if not youtube_source:
            if "id=" in path:
                video_id = path.split("id=")[-1]
            else:
                video_id = path.split("/preview")[0].split("/")[-1]
            path = "https://drive.google.com/uc?authuser=0&export=download&id={}".format(video_id)
    else:
        base_source = os.path.join(self.builder.srcdir, os.path.dirname(self.builder.current_docname))
        base_path = os.path.join(self.builder.outdir, "_images")
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        img_path = os.path.join(base_path, os.path.basename(path))
        print("Copying video to ", img_path)
        copyfile(os.path.join(base_source, path), img_path)
        path = "../_images/" + os.path.basename(img_path)

    extension = os.path.splitext(node["path"])[-1][1:]
    if youtube_source:
        if "embed" in path or "youtu.be" in path:
            video_id = path.split("/")[-1]
        else:
            video_id = path.split("v=")[1]
            video_id = video_id.split("&")[0]

        if node["onplay"] != "":
            print("onplay event is not supported for Youtube source:", node["onplay"])

        html_block = """
        {centered_in}<iframe id="{video_id}" type="text/html" {width} {height}"
            src="https://www.youtube.com/embed/{video_id}?{autoplay}{loop}{muted}{playsinline}{nocontrols}&modestbranding=1"
            frameborder="0" allowFullScreen="allowFullScreen"></iframe>{centered_out}
        """.format(
            video_id=video_id,
            width='width="' + node["width"] + '"' if node["width"] else "",
            height='height="' + node["height"] + '"' if node["height"] else "",
            autoplay="&autoplay=1" if node["autoplay"] else "",
            nocontrols="&controls=0" if node["nocontrols"] else "",
            loop="&loop=1&playlist={}".format(video_id) if node["loop"] else "",
            playsinline="&playsinline=1" if node["playsinline"] else "",
            muted="&mute=1" if node["muted"] else "",
            centered_in="<center>" if node["centered"] else "",
            centered_out="</center>" if node["centered"] else "",
        )
    else:
        html_block = """
        {centered_in}<video {width} {height} {nocontrols} {autoplay} {loop} {playsinline} {muted} {onplay}>
        <source src="{path}" type="video/{filetype}">
        {alt}
        </video>
        {centered_out}
        """.format(
            width='width="' + node["width"] + '"' if node["width"] else "",
            height='height="' + node["height"] + '"' if node["height"] else "",
            path=path,
            filetype=node["_type"],
            alt=node["alt"],
            autoplay="autoplay" if node["autoplay"] else "",
            nocontrols="" if node["nocontrols"] else "controls",
            loop="loop" if node["loop"] else "",
            onplay="onplay='" + node["onplay"] + "'" if node["onplay"] else "",
            playsinline="playsinline" if node["playsinline"] else "",
            muted="muted" if node["muted"] else "",
            centered_in="<center>" if node["centered"] else "",
            centered_out="</center>" if node["centered"] else "",
        )
    self.body.append(html_block)


def depart_video_node(self, node):
    pass


def setup(app):
    app.add_node(video, html=(visit_video_node, depart_video_node))
    app.add_directive("video", Video)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
