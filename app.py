from textual.app import App
from textual.widgets import Log, Input, Button
from textual import work
from main import similiar_search, process_file


class contextualApp(App):
    CSS_PATH = "style.tcss"
    upload_mode = False

    def compose(self):
        yield Log(auto_scroll=True, id = "log")
        yield Input(
            placeholder = "Ask contextual",
            id = "input"    
        )
        yield Button(
            label="Upload",
            variant="primary", 
            id= "Upload"
        )
    def is_loading(self, id: str, state: bool)-> None:
        widget = self.query_one(f"#{id}")
        widget.loading = state  
    
    def update_ui(self, id, content):
        widget = self.query_one(f'#{id}')
        if id == "log":
            widget.write(content)
            self.is_loading("input", False)
        else:
            widget.placeholder = content

    def restore(self):
        pass

         
    def on_button_pressed(self, message: Button.Pressed)->None:
        button = self.query_one("#Upload")
        button.disabled = True

        search_bar = self.query_one("#input")
        search_bar.placeholder = "File Path"
        
        self.upload_mode = True
        
    def on_input_submitted(self, event: Input.Submitted)->None:
        if not self.upload_mode:
            event.input.clear()
            event.input.loading = True
            
            self.make_question(event.value)

        else:
            event.input.clear()
            event.input.loading = True
            self.upload_file(event.value)
            
            self.upload_mode = False

            button = self.query_one("#Upload")
            button.disabled = False

     
    @work(exclusive=True, thread=True)
    def make_question(self, question):
        if question:
            response = similiar_search(question)
        
            self.call_from_thread(self.update_ui, response)

    @work(exclusive=True, thread=True)
    def upload_file(self,path: str):
        if path:
            try:
                process_file(path)
                self.call_from_thread(self.is_loading, "input", False)
                self.call_from_thread(
                    self.update_ui,
                    id = "log", 
                    content="File Uploaded"
                )

            except FileNotFoundError as e:
                self.call_from_thread(
                    self.update_ui, 
                    id = "log", 
                    content = str(e)
                )
                self.call_from_thread(
                    self.update_ui, 
                    id = "input", 
                    content = "Ask Contextual"
                )


if __name__ == "__main__":
    app = contextualApp()

    app.run()        
