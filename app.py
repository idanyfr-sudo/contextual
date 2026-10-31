from textual.app import App
from textual.widgets import Log, Input, Button
from textual import work
from main import similiar_search, process_file
from textual.reactive import reactive


class contextualApp(App):
    CSS_PATH = "style.tcss"
    upload_mode = reactive(False)

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
    
    def update_chat(self, content):
        widget = self.query_one("#log")
        
        widget.write(content)
        self.is_loading("input", False)
    

    def watch_upload_mode(self, new):
        search_bar = self.query_one("#input")
        button = self.query_one("#Upload")
        if new:
            search_bar.placeholder = "Upload mode: File Path"
            button.disabled = new   
        else:
            search_bar.placeholder = "Ask contextual"
            button.disabled = new  

         
    def on_button_pressed(self, message: Button.Pressed)->None:
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
     
    @work(exclusive=True, thread=True)
    def make_question(self, question):
        if question:
            response = similiar_search(question)
        
            self.call_from_thread(self.update_chat, content = response)

    @work(exclusive=True, thread=True)
    def upload_file(self,path: str):
        if path:
            try:
                process_file(path)

                self.call_from_thread(
                    self.update_chat,
                    content="File Uploaded"
                )

            except FileNotFoundError as e:
                self.call_from_thread(
                    self.update_chat, 
                    content = str(e)
                )

if __name__ == "__main__":
    app = contextualApp()

    app.run()        
