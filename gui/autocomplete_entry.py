import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Callable, Optional

class AutocompleteEntry(ttk.Frame):
    """
    Entry widget with autocomplete dropdown functionality
    """
    
    def __init__(self, parent, search_function: Callable[[str], List[Tuple[str, str]]], 
                 on_selection: Optional[Callable[[str, str], None]] = None, **kwargs):
        super().__init__(parent)
        
        self.search_function = search_function
        self.on_selection = on_selection
        self.suggestions = []
        
        # Create the entry widget
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.entry_var, **kwargs)
        self.entry.pack(fill="x")
        
        # Create dropdown listbox (initially hidden)
        self.dropdown_frame = tk.Toplevel(self)
        self.dropdown_frame.withdraw()
        self.dropdown_frame.wm_overrideredirect(True)
        self.dropdown_frame.configure(bg="white", relief="solid", borderwidth=1)
        
        # Create scrollable listbox
        self.listbox_frame = ttk.Frame(self.dropdown_frame)
        self.listbox_frame.pack(fill="both", expand=True)
        
        self.listbox = tk.Listbox(self.listbox_frame, height=6, 
                                 selectmode="single", relief="flat",
                                 font=("Arial", 9))
        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", 
                                      command=self.listbox.yview)
        
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.entry_var.trace("w", self.on_text_change)
        self.entry.bind("<KeyPress>", self.on_key_press)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        
        # Bind multiple events for listbox selection
        self.listbox.bind("<Button-1>", self.on_listbox_click)
        self.listbox.bind("<ButtonRelease-1>", self.on_listbox_release)
        self.listbox.bind("<Return>", self.on_listbox_select)
        self.listbox.bind("<Double-Button-1>", self.on_listbox_select)
        
        # Prevent dropdown from closing when mouse enters
        self.dropdown_frame.bind("<Enter>", self.on_dropdown_enter)
        self.dropdown_frame.bind("<Leave>", self.on_dropdown_leave)
        self.listbox.bind("<Enter>", self.on_dropdown_enter)
        self.listbox.bind("<Leave>", self.on_dropdown_leave)
        
        # Track if dropdown is visible and mouse state
        self.dropdown_visible = False
        self.mouse_in_dropdown = False
    
    def get(self) -> str:
        """Get the current text value"""
        return self.entry_var.get()
    
    def set(self, value: str):
        """Set the text value"""
        self.entry_var.set(value)
    
    def focus(self):
        """Focus the entry widget"""
        self.entry.focus()
    
    def on_text_change(self, *args):
        """Handle text changes in the entry"""
        text = self.entry_var.get().strip()
        
        if len(text) >= 2:  # Start searching after 2 characters for better performance
            self.suggestions = self.search_function(text)
            
            if self.suggestions:
                self.show_dropdown()
                self.update_listbox()
            else:
                self.hide_dropdown()
        elif len(text) == 0:
            self.hide_dropdown()
    
    def on_key_press(self, event):
        """Handle key presses"""
        if event.keysym == "Down" and self.dropdown_visible:
            # Move focus to listbox
            self.listbox.focus()
            if self.listbox.size() > 0:
                self.listbox.selection_set(0)
            return "break"
        elif event.keysym == "Escape":
            self.hide_dropdown()
        elif event.keysym == "Return" and not self.dropdown_visible:
            # If no dropdown, trigger selection with current text
            if self.on_selection:
                text = self.entry_var.get().strip()
                self.on_selection(text, text)
    
    def on_focus_out(self, event):
        """Hide dropdown when focus is lost (with delay to allow clicks)"""
        if event.widget == self.entry:
            # Much longer delay to allow for mouse selection
            self.after(800, self.hide_dropdown_if_not_clicking)
    
    def on_dropdown_enter(self, event):
        """Mouse entered dropdown area"""
        self.mouse_in_dropdown = True
    
    def on_dropdown_leave(self, event):
        """Mouse left dropdown area"""
        self.mouse_in_dropdown = False
        # Small delay before hiding to prevent flicker
        self.after(200, self.check_hide_dropdown)
    
    def on_listbox_click(self, event):
        """Handle mouse press on listbox - mark selection"""
        # Get the index where the user clicked
        index = self.listbox.nearest(event.y)
        if 0 <= index < self.listbox.size():
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
    
    def on_listbox_release(self, event):
        """Handle mouse release on listbox - complete selection"""
        self.on_listbox_select(event)
    
    def on_listbox_select(self, event):
        """Handle selection from listbox"""
        try:
            selection = self.listbox.curselection()
            if selection:
                index = selection[0]
                if index < len(self.suggestions):
                    symbol, company = self.suggestions[index]
                    self.entry_var.set(symbol)
                    
                    # Trigger callback
                    if self.on_selection:
                        self.on_selection(symbol, company)
                    
                    self.hide_dropdown()
                    self.entry.focus()
                    return "break"
            else:
                # If no selection, try to get the nearest item
                index = self.listbox.nearest(event.y) if hasattr(event, 'y') else 0
                if 0 <= index < len(self.suggestions):
                    symbol, company = self.suggestions[index]
                    self.entry_var.set(symbol)
                    
                    if self.on_selection:
                        self.on_selection(symbol, company)
                    
                    self.hide_dropdown()
                    self.entry.focus()
        except (IndexError, AttributeError) as e:
            print(f"Selection error: {e}")
            pass
    
    def show_dropdown(self):
        """Show the dropdown with suggestions"""
        if not self.dropdown_visible and self.suggestions:
            try:
                # Position dropdown below the entry
                self.update_idletasks()
                x = self.entry.winfo_rootx()
                y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
                width = max(self.entry.winfo_width(), 300)  # Minimum width
                
                # Calculate height based on number of suggestions
                max_height = min(len(self.suggestions) * 20 + 10, 200)
                
                self.dropdown_frame.geometry(f"{width}x{max_height}+{x}+{y}")
                self.dropdown_frame.deiconify()
                self.dropdown_frame.lift()
                self.dropdown_frame.focus_set()
                
                self.dropdown_visible = True
            except Exception as e:
                print(f"Error showing dropdown: {e}")
    
    def hide_dropdown(self):
        """Hide the dropdown"""
        if self.dropdown_visible:
            self.dropdown_frame.withdraw()
            self.dropdown_visible = False
    
    def hide_dropdown_if_not_clicking(self):
        """Hide dropdown only if not currently clicking on it"""
        # Don't hide if mouse is in dropdown
        if self.mouse_in_dropdown:
            return
        
        # Check if the mouse is over the dropdown
        try:
            x, y = self.dropdown_frame.winfo_pointerxy()
            widget = self.dropdown_frame.winfo_containing(x, y)
            if widget is None or widget not in [self.listbox, self.dropdown_frame, self.listbox_frame]:
                self.hide_dropdown()
        except:
            # If there's any error, just hide the dropdown
            self.hide_dropdown()
    
    def check_hide_dropdown(self):
        """Check if dropdown should be hidden after mouse leave"""
        if not self.mouse_in_dropdown and not self.entry.focus_get() == self.entry:
            self.hide_dropdown()
    
    def update_listbox(self):
        """Update listbox with current suggestions"""
        self.listbox.delete(0, tk.END)
        
        for symbol, company in self.suggestions:
            # Format display text
            display_text = f"{symbol} - {company}"
            if len(display_text) > 60:  # Truncate long company names
                display_text = display_text[:57] + "..."
            self.listbox.insert(tk.END, display_text)
    
    def destroy(self):
        """Clean up when destroying the widget"""
        if self.dropdown_frame:
            self.dropdown_frame.destroy()
        super().destroy()