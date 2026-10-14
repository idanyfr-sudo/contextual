from textual.app import App
from textual.widgets import Log, Input, Button
from textual import work
from main import similiar_search, process_file


class contextualApp(App):
    CSS_PATH = "style.tcss"

    def compose(self):
        yield Log(auto_scroll=True, id = "log")
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
            event.input.clear()
            self.make_question(event.value)

        else:
            event.input.clear()
            self.upload_file(event.value)  
    
    @work(exclusive=True, thread=True)
    def make_question(self,question: str):
        if question:
            response = similiar_search(question)
            text_box = self.query_one("#log")
            
            text_box.write(response)
    
    @work(exclusive=True, thread=True)
    def upload_file(self,path: str):
        if path:
            process_file(path)



        

            



if __name__ == "__main__":
    app = contextualApp()

    app.run()        