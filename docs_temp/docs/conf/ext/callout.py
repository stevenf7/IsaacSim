from re import search

from docutils import nodes
from docutils.parsers.rst import Directive, directives


# Author: Roman Sharf
# This is an Extension for generating release highlights callouts
# It works but is not currently in use. I will try using existing repo docs functionality
# instead of this. I'm keeping this here for reference.
class Callout(Directive):

    has_content = True

    # We can have two options in this directive
    option_spec = {
        "product": directives.unchanged,
        "heading_level": directives.unchanged,
        "link": directives.unchanged,
    }

    def run(self):

        if "product" not in self.options:
            raise self.error("You need to supply the :product: option when using the callout directive.")

        if "heading_level" not in self.options:
            raise self.error("You need to supply the :heading_level: option when using the callout directive.")

        if "link" not in self.options:
            raise self.error("You need to supply the :link: option when using the callout directive.")

        product = self.options.get("product")

        heading_level = self.options.get("heading_level")

        link = self.options.get("link")

        # Get the content values
        custom_text = self.content

        res = []

        # Parse the content so that it's usable
        for line in custom_text:
            end_result = search(r"[\"\'](.*)?[\"\'],(?:\s)*?[\"\'](.*)?[\"\'],(?:\s)*?[\"\'](.*)?[\"\']", line)
            end_result = (end_result.group(1), end_result.group(2), end_result.group(3))
            res.append(end_result)

        # Define the HTML code and use the content the user provided
        html_code = f"""
        
        <h{heading_level}>What's new in {product}?</h{heading_level}>
        <div class='rh_callouts'>

        <p>Read about the latest features in {product}</p>
        
        <div class='rh_cards'>
            <a href='{link}#{res[0][2]}'>
                <h3>{res[0][0]}</h3>
                <p>{res[0][1]}</p>
            </a>
            
            <a href='{link}#{res[1][2]}'>
                <h3>{res[1][0]}</h3>
                <p>{res[1][1]}</p>
            </a>
            
            <a href='{link}#{res[2][2]}'>
                <h3>{res[2][0]}</h3>
                <p>{res[2][1]}</p> 
            </a>
        </div>

        <a href='#' class='button'>View All Release Highlights</a>
        </div>
        <br/>
        """

        # Create an HTML element node with the predefined HTML and content
        html_node = nodes.raw("", html_code, format="html")

        # If the user provided a :depth: option in the directive, insert a heading section and alter its level/depth. Otherwise, do not insert a heading.
        return [html_node]


def setup(app):
    app.add_directive("callout", Callout)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
