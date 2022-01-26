from tkinter import *
from tkinter import ttk
from typing import Optional

from db import LockableSqliteConn
from configure import command

def get_properties(lconn: LockableSqliteConn, property: Optional[str] = None) -> tuple:
	with lconn:
		if property:
			lconn.cur.execute('''SELECT * FROM properties WHERE property = ?;''', (property,))
			return lconn.cur.fetchone()
		else:
			lconn.cur.execute('''SELECT * FROM properties;''')
			return lconn.cur.fetchall()

def get_property_settings(lconn: LockableSqliteConn, property: Optional[str] = None) -> tuple:
	with lconn:
		if property:
			lconn.cur.execute('''SELECT * FROM property_settings WHERE property = ?;''', (property,))
			return lconn.cur.fetchone()
		else:
			lconn.cur.execute('''SELECT * FROM property_settings;''')
			return lconn.cur.fetchall()

def get_destinations(lconn: LockableSqliteConn, user_at_ip: Optional[str] = None) -> tuple:
	with lconn:
		if user_at_ip:
			lconn.cur.execute('''SELECT * FROM destination_servers WHERE user_at_ip = ?;''', (user_at_ip,))
			return lconn.cur.fetchone()
		else:
			lconn.cur.execute('''SELECT * FROM destination_servers;''')
			return lconn.cur.fetchall()


class RootWindow:
	def __init__(self, lconn: LockableSqliteConn):
		self.lconn = lconn

		# Build window
		self.root = Tk()
		self.root.title('Media Processor Configurator')
		self.root.minsize(500, 500)
		self.root.grid_columnconfigure(0, weight=1)
		self.root.grid_rowconfigure(0, weight=1)

		main_frame = Frame(self.root)
		main_frame.grid(row=0, column=0, sticky=N)
	
		# Add property listings and action buttons
		property_frame = Frame(main_frame)
		property_frame.grid(row=0, column=0, pady=10)
		self.property_listbox = Listbox(property_frame)
		self.property_listbox.grid(row=0, column=0)
		property_listbox_scroll = Scrollbar(property_frame)
		property_listbox_scroll.grid(row=0, column=1, sticky=N+S+W)
		self.property_listbox.config(yscrollcommand=property_listbox_scroll.set)
		property_listbox_scroll.config(command=self.property_listbox.yview)
		property_actions_frame = Frame(main_frame)
		property_actions_frame.grid(row=0, column=1)
		Button(property_actions_frame, text='Add/Edit property', command=lambda: AddEditPropertyWindow(self)).grid(row=0, column=0)
		Button(property_actions_frame, text='Remove property').grid(row=1, column=0)

		for i, row in enumerate(get_properties(self.lconn)):
			self.property_listbox.insert(i, row[0])

		# Add destination listings and action buttons
		destination_frame = Frame(main_frame)
		destination_frame.grid(row=1, column=0, pady=10)
		self.destination_listbox = Listbox(destination_frame)
		self.destination_listbox.grid(row=0, column=0)
		destination_listbox_scroll = Scrollbar(destination_frame)
		destination_listbox_scroll.grid(row=0, column=1, sticky=N+S+W)
		self.destination_listbox.config(yscrollcommand=property_listbox_scroll.set)
		property_listbox_scroll.config(command=self.destination_listbox.yview)
		destination_actions_frame = Frame(main_frame)
		destination_actions_frame.grid(row=1, column=1)
		Button(destination_actions_frame, text='Add/Edit destination server').grid(row=0, column=0)
		Button(destination_actions_frame, text='Remove destination server').grid(row=1, column=0)

		for i, row in enumerate(get_destinations(lconn)):
			self.destination_listbox.insert(i, row[0])
	
		# Add action button(s)
		action_frame = Frame(self.root)
		action_frame.grid(row=2, column=0, sticky=SE)
		Button(action_frame, text='Exit', command=lambda: self.root.quit()).grid(row=0, column=0, padx=5)
	
		self.root.mainloop()


class AddEditPropertyWindow:
	def __init__(self, root_window: RootWindow) -> None:
		self.root_window = root_window

		# Build window
		self.add_edit_window = Toplevel()
		self.add_edit_window.minsize(500, 500)
		self.add_edit_window.title('Media Processor Configurator | Add Edit Property')
		self.add_edit_window.grid_columnconfigure(0, weight=1)
		self.add_edit_window.grid_rowconfigure(0, weight=1)

		main_frame = Frame(self.add_edit_window)
		main_frame.grid(row=0, column=0, sticky=N)

		property_frame = Frame(main_frame)
		property_frame.grid(row=0, column=0, pady=10)
		Label(property_frame, text='Property').grid(row=0, column=0, columnspan=2)
		Label(property_frame, text='Property:').grid(row=1, column=0)
		self.property_entry = Entry(property_frame)
		self.property_entry.grid(row=1, column=1)
		Label(property_frame, text='Pattern:').grid(row=2, column=0)
		self.pattern_entry = Entry(property_frame)
		self.pattern_entry.grid(row=2, column=1)
		self.partial_var = IntVar()
		partial_checkbox = Checkbutton(property_frame, text='Partial?', variable=self.partial_var)
		partial_checkbox.grid(row=3, column=0, columnspan=2)

		settings_frame = Frame(main_frame)
		settings_frame.grid(row=3, column=0, pady=10)
		Label(settings_frame, text='Settings').grid(row=0, column=0, columnspan=2)
		Label(settings_frame, text='FFMPEG Args:').grid(row=1, column=0)
		self.ffmpeg_args_entry = Entry(settings_frame)
		self.ffmpeg_args_entry.grid(row=1, column=1)
		Label(settings_frame, text='Output Container:').grid(row=2, column=0)
		self.output_container_entry = Entry(settings_frame)
		self.output_container_entry.grid(row=2, column=1)
		Label(settings_frame, text='Folder:').grid(row=3, column=0)
		self.folder_entry = Entry(settings_frame)
		self.folder_entry.grid(row=3, column=1)
		Label(settings_frame, text='Destination Server (leave blank for local):').grid(row=4, column=0)
		with self.root_window.lconn:
			self.root_window.lconn.cur.execute('''SELECT user_at_ip FROM destination_servers;''')
			user_at_ips = list(map(lambda uai: uai[0], self.root_window.lconn.cur.fetchall()))
		self.destination_server_box = ttk.Combobox(settings_frame, values=user_at_ips)
		self.destination_server_box.grid(row=4, column=1)
		self.is_show_var = IntVar()
		is_show_checkbox = Checkbutton(settings_frame, text='Is Show?', variable=self.is_show_var)
		is_show_checkbox.grid(row=5, column=0, columnspan=2)
		Label(settings_frame, text='Season Override (leave blank for auto):').grid(row=6, column=0)
		self.season_override_entry = Entry(settings_frame)
		self.season_override_entry.grid(row=6, column=1)

		action_frame = Frame(self.add_edit_window)
		action_frame.grid(row=4, column=0, sticky=SE)
		Button(action_frame, text='Save and Exit', command=self.save_and_exit).grid(row=0, column=0, padx=5)

	def get_settings(self) -> dict:
		'''Get the settings as a dict of dicts representing the DB entries'''
		prop = self.property_entry.get()
		return {
			'properties': {
				'property': prop,
				'pattern': self.pattern_entry.get(),
				'partial': self.partial_var.get()
			},
			'settings': {
				'property': prop,
				'ffmpeg_args': self.ffmpeg_args_entry.get(),
				'output_container': self.output_container_entry.get(),
				'folder': self.folder_entry.get(),
				'user_at_ip': self.destination_server_box.get(),
				'is_show': self.is_show_var.get(),
				'season_override': self.season_override_entry.get()
			}
		}

	def save_and_exit(self) -> None:
		'''Save changes and close TopLevel'''
		# TODO: save settings to db
		self.add_edit_window.destroy()

	# selected_property: Optional[str] = listbox.get(listbox.curselection()[0]) if len(listbox.curselection()) > 0 else None
	# if selected_property:
	# 	pass
	# else:
	# 	pass


def driver(lconn: LockableSqliteConn) -> None:
	RootWindow(lconn)