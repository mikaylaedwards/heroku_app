from threading import Thread

from flask import Flask, render_template,request
from tornado.ioloop import IOLoop
import pandas as pd
from bokeh.plotting import figure
from bokeh.embed import components,server_document
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.server.server import Server
from bokeh.palettes import RdBu3,Spectral5
from bokeh.transform import factor_cmap

app = Flask(__name__)

# Load the Marketing Data Set
marketing=pd.read_csv("data/marketing_new.csv",index_col=0)
feature_names = ['marketing_channel','subscribing_channel','age_group']

# Create the main plot
def get_conversion_rate(df,grouping):
    num_convs=df[df['converted'] == True]\
                       .groupby(grouping)['user_id'].nunique().rename('num_converted')

    total = df.groupby(grouping)['user_id'].nunique().rename('num_total')

    conv_rate=pd.merge(num_convs,total,left_index=True,right_index=True,how='outer')\
        .assign(not_conv=lambda x: x['num_total']-x['num_converted'],conv_rate=lambda x: x['num_converted']/x['num_total'])\
        .fillna(0)
    return conv_rate.reset_index()


def make_plot(df,col_name):
    
    grouped=get_conversion_rate(df,[col_name])
    
    source = ColumnDataSource(grouped)
    group=source.data[col_name].tolist()

    group_cmap = factor_cmap(col_name, palette=Spectral5, factors=sorted(grouped[col_name].unique()))

    title="Conversion by: " + col_name
    p = figure(plot_height=350, x_range=group, title=title)

    p.vbar(x=col_name, top='num_converted', width=1,
       line_color=group_cmap, fill_color=group_cmap,source=source)
        
    p.y_range.start = 0
    p.xgrid.grid_line_color = None
    p.xaxis.axis_label =col_name
    p.xaxis.major_label_orientation = 1.2
    p.outline_line_color = None
    
    return p

# Index page
@app.route('/')
def index():
    # Determine the selected feature
    current_feature_name = request.args.get("feature_name")
    if current_feature_name == None:
        current_feature_name = "marketing_channel"

    # Create the plot
    plot = make_plot(marketing,current_feature_name)

# Embed plot into HTML via Flask Render
    script, div = components(plot)
    return render_template("m_index.html", script=script, div=div,
        feature_names=feature_names,  current_feature_name=current_feature_name)

# With debug=True, Flask server will auto-reload 
# when there are code changes
if __name__ == '__main__':
    app.run(port=5000, debug=True)


