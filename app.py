from textual.app import App
from textual.widgets import Log, Input, Button
from main import similiar_search, load_file


class contextualApp(App):
    CSS_PATH = "style.tcss"

    def compose(self):
        yield Log(auto_scroll=False, id = "log")
        yield Input(
            placeholder="Ask contextual",
            id = "input"    
        )
        yield Button(
            label="Upload", 
            variant="primary", 
            id= "Upload"
        )

    
    def on_button_pressed(self, message: Button.Pressed)->None:
        button = self.query_one("#Upload")
        button.remove()
        
        self.mount(Input(placeholder = "File path", id ="InputPath"))
    
    def on_input_submitted(self, event: Input.Submitted)->None:
        if event.input.id == "input":
            response = similiar_search(event.value)
            text_box = self.query_one("#log")

            text_box.write(response)
        else:
            load_file(event.value)



if __name__ == "__main__":
    app = contextualApp()

    app.run()        


    




