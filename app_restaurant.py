from shiny.express import ui, input, render
from shiny import reactive
import seaborn as sns
import plotly.express as px
from shinywidgets import render_plotly, render_widget
from ridgeplot import ridgeplot


tips = sns.load_dataset("tips")


@reactive.calc
def tips_filtered():
    total_lower = input.tip_range()[0]
    total_upper = input.tip_range()[1]
    idx1 = tips.total_bill.between(left=total_lower, right=total_upper, inclusive="both")
    idx2 = tips.time.isin(input.time_selected())
    
    return tips[idx1 & idx2]

@reactive.effect
@reactive.event(input.action_button)
def reset_filter_button():
    ui.update_slider("tip_range", value=(tips.total_bill.min(), tips.total_bill.max()))
    ui.update_checkbox_group("time_selected", selected=["Lunch", "Dinner"])

ui.page_opts(title="Restaurant Tipping", fillable=True)

with ui.sidebar(id="sidebar_left", open="desktop"):
    ui.input_slider(
        id="tip_range", 
        label="Tip Range:", 
        min = tips.total_bill.min(), 
        max = tips.total_bill.max(), 
        value = (tips.total_bill.min(), tips.total_bill.max()), step=0.1)
    ui.input_checkbox_group(
        id="time_selected",
        label="Food service",
        choices={
            "Lunch": "Lunch",
            "Dinner": "Dinner",
        },
        selected=[
            "Lunch",
            "Dinner",
        ],
    )
    ui.input_action_button("action_button", "Reset Filters")

with ui.layout_columns(col_widths=[4,4,4], fill=False):
    with ui.value_box():
        "Total Tippers:"
        @render.text
        def total_tippers():
            return tips_filtered().shape[0]
        
    with ui.value_box():
        "Average Tip:"
        @render.text
        def average_tip():
            tip_pct = (tips_filtered().tip / tips_filtered().total_bill).mean()
            return f"{tip_pct:.1%}"
        
    with ui.value_box():
        "Average Bill:"
        @render.text
        def average_bill():
            return tips_filtered().total_bill.mean().round(2)
        


with ui.layout_columns(col_widths=[6,6], fill=False):
    with ui.card():
        ui.card_header("Tips Data:")
        @render.data_frame
        def tips_data():
            return tips_filtered()
        
    with ui.card():
        ui.card_header("Total Bill vs Tip:")
        @render_plotly
        def tips_vs_bill():
            fig = px.scatter(
                tips_filtered(), 
                x="total_bill", 
                y="tip",
                trendline="ols"
            )
            return fig
        

with ui.layout_columns(fill=False):
    with ui.card(full_screen=True):
        ui.card_header("Tip Percentages:")
        @render_widget
        def ridge():
            tips_filtered()["percent"] = tips_filtered().tip / tips_filtered().total_bill

            uvals = tips_filtered().day.unique()
            samples = [[tips_filtered().percent[tips_filtered().day == val]] for val in uvals]

            plt = ridgeplot(
                samples=samples,
                labels=uvals,
                bandwidth=0.01,
                colorscale="viridis",
                colormode="row-index"
            )

            plt.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )

            return plt