# This script takes three input files and combines them into a big explorer spreadsheet for the global food explorer.
# The files are:
# - (1) global-food-explorer.template.tsv: A template file that contains the header and footer of the spreadsheet, together with some placeholders.
# - (2) foods.tsv: a list of foods and their singular and plural names.
# - (3) views-per-food.tsv: a list of all available views for every food, including subtitle etc. The title can contain placeholders which are then filled out with the food name.
# We take the cartesian product between (2) and (3), sprinkle some magic dust to make the titles work, and then write place that massive table into the template (1).

# %%
from string import Template
import pandas as pd
import textwrap
import random

# %%


def food_url(food):
    return f"https://gist.githubusercontent.com/MarcelGerber/7011dc7aa5fee1e77a3a7ca2fbc30b37/raw/b3d151199b9f406622e146fa625f19b333d89923/{food}.csv"


def substitute_title(row):
    # The title can include placeholders like ${food_singular_title}, which will be replaced with the actual food name here.
    food_slug = row['tableSlug']
    food_names = foods_df.loc[food_slug]
    template = Template(row['title'])
    row['title'] = template.substitute(
        food_singular_title=food_names['singular'],
        food_singular_lower=food_names['singular'].lower(),
        food_plural_title=food_names['plural'],
        food_plural_lower=food_names['plural'].lower(),
    )
    return row


def table_def(food):
    # return f"table\t{food_url(food)}\t{food}"
    return f"table\t{food_url('apples' if random.randint(0, 1) == 0 else 'bananas')}\t{food}"


# %%
with open('global-food-explorer.template.tsv', 'r') as templateFile:
    template = Template(templateFile.read())
foods_df = pd.read_csv('foods.tsv', sep='\t', index_col='slug')
views_df = pd.read_csv('views-per-food.tsv', sep='\t', dtype=str)

# %%
foods = pd.DataFrame([{'Food Dropdown': row['dropdown'], 'tableSlug': slug}
                     for slug, row in foods_df.iterrows()])

# %%
graphers = foods.merge(views_df, how='cross').apply(substitute_title, axis=1)

# %%
# We want to have a consistent column order for easier interpretation of the output.
# However, if there are any columns added to the views tsv at any point in the future,
# we want to make sure these are also present in the output.
# Therefore, we define the column order and also add any remaining columns to the output.
col_order = ['title', 'Food Dropdown', 'Metric Dropdown', 'Unit Radio',
             'Per Capita Checkbox', 'subtitle', 'type', 'ySlugs', 'tableSlug', 'hasMapTab']
remaining_cols = pd.Index(graphers.columns).difference(
    pd.Index(col_order)).tolist()
graphers = graphers.reindex(columns=col_order + remaining_cols)

# %%
graphers_tsv = graphers.to_csv(sep='\t', index=False)
graphers_tsv_indented = textwrap.indent(graphers_tsv, '\t')

table_defs = '\n'.join([table_def(food) for food in foods_df.index])
table_slugs = '\t'.join(foods_df.index)

# %%
with open('../../explorers/global-food-prototype.explorer.tsv', 'w', newline='\n') as f:
    f.write(template.substitute(
        graphers_tsv=graphers_tsv_indented,
        table_defs=table_defs,
        table_slugs=table_slugs
    ))
