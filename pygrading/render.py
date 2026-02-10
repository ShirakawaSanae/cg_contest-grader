"""
    Name: render.py
    Author: Charles Zhang <694556046@qq.com>
    Propose: Render a html template support Bootstrap4.
    Coding: UTF-8
"""

from jinja2 import Environment, PackageLoader, select_autoescape


class Render(object):

    def __init__(self, package_name: str, package_path: str):

        self.env = Environment(
            loader=PackageLoader(package_name, package_path),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render(self, template_name, **args):
        return self.env.get_template(template_name).render(args)


def render_template(template_name="index.html", package_name="templates", package_path="html", **args):

    render = Render(package_name, package_path)

    return render.render(template_name, **args)
