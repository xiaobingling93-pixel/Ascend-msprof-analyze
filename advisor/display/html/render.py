import os
import logging
from typing import List, Dict
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader
from profiler.advisor.common import constant

from profiler.advisor.config.config import Config
from profiler.advisor.utils.utils import singleton, safe_write

logger = logging.getLogger()


@singleton
class HTMLRender:
    def __init__(self):
        self.html = ""
        self.render_list = defaultdict(list)

    def render_html(self, template_dir: str = "templates", template_name: str = "main.html",
                    template_header=constant.DEFAULT_TEMPLATE_HEADER):
        self.html = self.render_template("main", template_dir, template_name, render_list=self.render_list,
                                         template_header=template_header)

    def render_template(self, key: str, template_dir: str, template_name: str, **kwargs):
        if not os.path.isabs(template_dir):
            template_dir = os.path.join(os.path.dirname(__file__), template_dir)

        env = Environment(loader=FileSystemLoader(template_dir),
                          autoescape=True)
        template = env.get_template(template_name)
        rendered_html = template.render(**kwargs)
        self.render_list[key].append(rendered_html)
        return rendered_html

    def save_to_file(self, save_path: str):
        if not save_path.endswith(".html"):
            logger.error("Skip save html file because file name must endswith `.html`, "
                         "but got %s.", os.path.basename(save_path))
            return

        safe_write(self.html, save_path)
        logger.info("Save suggestion to %s.", os.path.join(Config().work_path, save_path))
