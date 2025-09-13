import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, timedelta
from typing import Optional, Callable

class DatePicker:
    def __init__(self, parent, initial_date: str = None, callback: Optional[Callable] = None):
        """
        Calendar-based date picker widget
        
        Args:
            parent: Parent widget
            initial_date: Initial date in YYYY-MM-DD format
            callback: Function to call when date is selected
        """
        self.parent = parent
        self.callback = callback
        self.selected_date = initial_date or datetime.now().strftime("%Y-%m-%d")
        
        # Parse initial date
        try:
            self.current_date = datetime.strptime(self.selected_date, "%Y-%m-%d")
        except ValueError:
            self.current_date = datetime.now()
            self.selected_date = self.current_date.strftime("%Y-%m-%d")
        
        self.popup = None
        self.create_widget()
    
    def create_widget(self):
        """Create the main date picker widget (entry + button)"""
        self.frame = ttk.Frame(self.parent)
        
        # Date entry field
        self.date_var = tk.StringVar(value=self.selected_date)
        self.date_entry = ttk.Entry(self.frame, textvariable=self.date_var, width=12)
        self.date_entry.pack(side="left", padx=(0, 2))
        
        # Calendar button
        self.calendar_btn = ttk.Button(self.frame, text="📅", width=3,
                                      command=self.show_calendar)
        self.calendar_btn.pack(side="left")
        
        # Bind entry validation
        self.date_entry.bind('<Return>', self.validate_entry)
        self.date_entry.bind('<FocusOut>', self.validate_entry)
    
    def get_widget(self):
        """Return the main widget frame"""
        return self.frame
    
    def get_date(self):
        """Get the currently selected date"""
        return self.date_var.get()
    
    def set_date(self, date_str: str):
        """Set the date"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            self.date_var.set(date_str)
            self.selected_date = date_str
        except ValueError:
            pass
    
    def validate_entry(self, event=None):
        """Validate manually entered date"""
        try:
            entered_date = self.date_var.get().strip()
            datetime.strptime(entered_date, "%Y-%m-%d")
            self.selected_date = entered_date
            if self.callback:
                self.callback(entered_date)
        except ValueError:
            # Reset to previous valid date
            self.date_var.set(self.selected_date)
    
    def show_calendar(self):
        """Show calendar popup"""
        if self.popup:
            return
            
        self.popup = tk.Toplevel(self.parent)
        self.popup.title("Select Date")
        self.popup.resizable(False, False)
        self.popup.grab_set()
        
        # Position popup near the button
        x = self.calendar_btn.winfo_rootx()
        y = self.calendar_btn.winfo_rooty() + self.calendar_btn.winfo_height()
        self.popup.geometry(f"+{x}+{y}")
        
        self.create_calendar()
        
        # Close on escape or click outside
        self.popup.bind('<Escape>', lambda e: self.close_calendar())
        self.popup.protocol("WM_DELETE_WINDOW", self.close_calendar)
    
    def create_calendar(self):
        """Create calendar widget"""
        # Header frame for navigation
        header_frame = ttk.Frame(self.popup)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Previous month button
        ttk.Button(header_frame, text="◀", width=3,
                  command=self.prev_month).pack(side="left")
        
        # Month/Year label
        self.month_year_var = tk.StringVar()
        month_label = ttk.Label(header_frame, textvariable=self.month_year_var,
                               font=("Arial", 10, "bold"))
        month_label.pack(side="left", expand=True)
        
        # Next month button
        ttk.Button(header_frame, text="▶", width=3,
                  command=self.next_month).pack(side="right")
        
        # Calendar frame
        cal_frame = ttk.Frame(self.popup)
        cal_frame.pack(padx=10, pady=5)
        
        # Day headers
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            label = ttk.Label(cal_frame, text=day, font=("Arial", 8, "bold"))
            label.grid(row=0, column=i, padx=1, pady=1)
        
        # Calendar grid
        self.day_buttons = []
        for week in range(6):  # 6 weeks max
            week_buttons = []
            for day in range(7):
                btn = tk.Button(cal_frame, text="", width=3, height=1,
                              font=("Arial", 8),
                              command=lambda w=week, d=day: self.select_date(w, d))
                btn.grid(row=week+1, column=day, padx=1, pady=1)
                week_buttons.append(btn)
            self.day_buttons.append(week_buttons)
        
        # Bottom frame with today and close buttons
        bottom_frame = ttk.Frame(self.popup)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ttk.Button(bottom_frame, text="Today",
                  command=self.select_today).pack(side="left")
        ttk.Button(bottom_frame, text="Close",
                  command=self.close_calendar).pack(side="right")
        
        self.update_calendar()
    
    def update_calendar(self):
        """Update calendar display"""
        # Update month/year display
        month_name = calendar.month_name[self.current_date.month]
        self.month_year_var.set(f"{month_name} {self.current_date.year}")
        
        # Get calendar data
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Clear all buttons
        for week_buttons in self.day_buttons:
            for btn in week_buttons:
                btn.config(text="", state="disabled", bg="SystemButtonFace")
        
        # Fill in the days
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                    
                btn = self.day_buttons[week_num][day_num]
                btn.config(text=str(day), state="normal")
                
                # Highlight selected date
                date_str = f"{self.current_date.year:04d}-{self.current_date.month:02d}-{day:02d}"
                if date_str == self.selected_date:
                    btn.config(bg="lightblue")
                else:
                    btn.config(bg="white")
    
    def prev_month(self):
        """Go to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year-1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1)
        self.update_calendar()
    
    def next_month(self):
        """Go to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year+1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1)
        self.update_calendar()
    
    def select_date(self, week, day):
        """Select a specific date"""
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        selected_day = cal[week][day]
        
        if selected_day != 0:
            date_str = f"{self.current_date.year:04d}-{self.current_date.month:02d}-{selected_day:02d}"
            self.selected_date = date_str
            self.date_var.set(date_str)
            
            if self.callback:
                self.callback(date_str)
            
            self.close_calendar()
    
    def select_today(self):
        """Select today's date"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.selected_date = today
        self.date_var.set(today)
        
        if self.callback:
            self.callback(today)
        
        self.close_calendar()
    
    def close_calendar(self):
        """Close calendar popup"""
        if self.popup:
            self.popup.destroy()
            self.popup = None

class DatePickerEntry(ttk.Frame):
    """A simple date picker that can be used like a regular Entry widget"""
    
    def __init__(self, parent, initial_date: str = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.date_picker = DatePicker(self, initial_date)
        self.date_picker.get_widget().pack(fill="both", expand=True)
    
    def get(self):
        """Get the selected date (mimics Entry.get())"""
        return self.date_picker.get_date()
    
    def set(self, date_str: str):
        """Set the date (mimics Entry.insert())"""
        self.date_picker.set_date(date_str)
    
    def bind_callback(self, callback):
        """Bind a callback function for date changes"""
        self.date_picker.callback = callback