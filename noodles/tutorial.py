"""
Functions useful for tutorial work and unit testing.
"""

from inspect import Parameter
from graphviz import Digraph
import html
import sys

from . import schedule, schedule_hint, get_workflow


@schedule
def echo_add(x, y):
    print('adding', x, 'and', y, file=sys.stderr)
    return x + y


@schedule
def add(x, y):
    """add `x` and `y`."""
    return x + y


@schedule_hint(display="{a} + {b}", confirm=True)
def log_add(a, b):
    """add `a` and `b` and send message to logger."""
    return a + b


@schedule
def sub(x, y):
    """subtract `y` from `x`."""
    return x - y


@schedule
def mul(x, y):
    """multiply `x` and `y`."""
    return x*y


@schedule
def accumulate(lst, start=0):
    """compute sum of `lst`."""
    return sum(lst, start)


def _format_arg_list(args, variadic=False):
    """Format a list of arguments for pretty printing.

    :param a: list of arguments.
    :type a: list

    :param v: tell if the function accepts variadic arguments
    :type v: bool
    """
    def sugar(s):
        """Shorten strings that are too long for decency."""
        s = s.replace("{", "{{").replace("}", "}}")
        if len(s) > 50:
            return s[:20] + " ... " + s[-20:]
        else:
            return s

    def arg_to_str(arg):
        """Convert argument to a string."""
        if isinstance(arg, str):
            return sugar(repr(arg))
        elif arg is Parameter.empty:
            return '\u2014'
        else:
            return sugar(str(arg))

    if not args:
        if variadic:
            return "(\u2026)"
        else:
            return "()"

    return "(" + ", ".join(map(arg_to_str, args)) + ")"


def get_workflow_graph(promise):
    """Get a graph of a promise."""
    workflow = get_workflow(promise)

    dot = Digraph()
    for i, n in workflow.nodes.items():
        dot.node(str(i), label="{0} \n {1}".format(
            n.foo.__name__,
            _format_arg_list(n.bound_args.args)))

    for i in workflow.links:
        for j in workflow.links[i]:
            dot.edge(str(i), str(j[0]), label=str(j[1].name))

    return dot


def display_workflows(prefix, **kwargs):
    """Display workflows in a table. This generates SVG files. Use this in a
    Jupyter notebook and ship the images

    :param prefix: name prefix for svg files generated.
    :param kwargs: keyword arguments containing a workflow each.
    """
    from IPython.display import display, Markdown

    def create_svg(name, workflow):
        """Create an SVG file with rendered graph from a workflow."""
        name = name.replace('_', '-')
        filename = '{}-{}.svg'.format(prefix, name)
        dot = get_workflow_graph(workflow)
        dot.attr('graph', bgcolor='transparent')
        with open(filename, 'bw') as file:
            file.write(dot.pipe(format='svg'))
        return name, filename

    svg_files = {name: svg for name, svg in
                 (create_svg(name, workflow)
                  for name, workflow in kwargs.items())}

    markdown_table = \
        '| ' + ' | '.join(svg_files.keys()) + ' |\n' + \
        '| ' + ' | '.join('---' for _ in svg_files) + ' |\n' + \
        '| ' + ' | '.join('![workflow {}]({})'.format(name, svg)
                          for name, svg in svg_files.items()) + ' |'
    display(Markdown(markdown_table))


def snip_line(line, max_width, split_at):
    """Shorten a line to a maximum length."""
    if len(line) < max_width:
        return line
    return line[:split_at] + " … " \
        + line[-(max_width - split_at - 3):]


def display_text(text, highlight=None, max_width=80, split_at=None):
    """In a Jupyter notebook, takes a multi-line string, displays these lines
    in '<pre></pre>' block HTML. A list of lines may be provided that should
    be highlighted in the result. A highlight gives a gray background and bold
    font.

    :param text: string
    :param lines: list of lines to be highlighted.
    """
    from IPython.display import display, HTML

    if not isinstance(text, str):
        text = str(text)

    highlight = highlight or []
    split_at = split_at or max_width - 10
    style = [
        'font-size: 9pt; margin: 0pt',
        'background: #eeeeee; color: black;'
        'font-weight: bold; font-size: 9pt; margin: 0pt']
    display(HTML('\n'.join(
        '<pre style="{}">{}</pre>'.format(
            style[i in highlight],
            html.escape(snip_line(line, max_width, split_at)))
        for i, line in enumerate(text.splitlines()))))


def run_and_print_log(workflow, highlight=None):
    """Run workflow on multi-threaded worker cached with Sqlite3.

    :param workflow: workflow to evaluate.
    :param highlight: highlight these lines.
    """
    from noodles.run.threading.sqlite3 import run_parallel
    from noodles import serial

    import io
    import logging

    log = io.StringIO()
    log_handler = logging.StreamHandler(log)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    log_handler.setFormatter(formatter)

    logger = logging.getLogger('noodles')
    logger.setLevel(logging.INFO)
    logger.handlers = [log_handler]

    result = run_parallel(
        workflow, n_threads=4, registry=serial.base, db_file='tutorial.db',
        always_cache=True, echo_log=False)
    display_text(log.getvalue(), highlight or [], split_at=40)
    return result
