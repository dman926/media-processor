from tkinter import *
from tkinter import ttk
from tkinter.messagebox import askyesno
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
		self.property_listbox.bind('<FocusOut>', lambda e: self.property_listbox.selection_clear(0, END))
		property_listbox_scroll = Scrollbar(property_frame)
		property_listbox_scroll.grid(row=0, column=1, sticky=N+S+W)
		self.property_listbox.config(yscrollcommand=property_listbox_scroll.set)
		property_listbox_scroll.config(command=self.property_listbox.yview)
		property_actions_frame = Frame(main_frame)
		property_actions_frame.grid(row=0, column=1)
		Button(property_actions_frame, text='Add/Edit property', command=lambda: AddEditPropertyWindow(self)).grid(row=0, column=0)
		Button(property_actions_frame, text='Remove property', command=self.remove_selected_property).grid(row=1, column=0)

		self.update_properties_list()

		# Add destination listings and action buttons
		destination_frame = Frame(main_frame)
		destination_frame.grid(row=1, column=0, pady=10)
		self.destination_listbox = Listbox(destination_frame)
		self.destination_listbox.grid(row=0, column=0)
		self.destination_listbox.bind('<FocusOut>', lambda e: self.destination_listbox.selection_clear(0, END))
		destination_listbox_scroll = Scrollbar(destination_frame)
		destination_listbox_scroll.grid(row=0, column=1, sticky=N+S+W)
		self.destination_listbox.config(yscrollcommand=property_listbox_scroll.set)
		property_listbox_scroll.config(command=self.destination_listbox.yview)
		destination_actions_frame = Frame(main_frame)
		destination_actions_frame.grid(row=1, column=1)
		Button(destination_actions_frame, text='Add/Edit destination server', command=lambda: AddEditDestinationWindow(self)).grid(row=0, column=0)
		Button(destination_actions_frame, text='Remove destination server', command=self.remove_selected_destination).grid(row=1, column=0)

		self.update_destinations_list()
	
		# Add action button(s)
		action_frame = Frame(self.root)
		action_frame.grid(row=2, column=0, sticky=SE)
		Button(action_frame, text='Exit', command=lambda: self.root.quit()).grid(row=0, column=0, padx=5)
	
		self.root.mainloop()

	def update_properties_list(self) -> None:
		self.property_listbox.delete(0, END)
		for i, row in enumerate(get_properties(self.lconn)):
			self.property_listbox.insert(i, row[0])

	def update_destinations_list(self) -> None:
		self.destination_listbox.delete(0, END)
		for i, row in enumerate(get_destinations(self.lconn)):
			self.destination_listbox.insert(i, row[0])

	def remove_selected_property(self) -> None:
		selected_property: Optional[str] = self.property_listbox.get(self.property_listbox.curselection()[0]) if len(self.property_listbox.curselection()) > 0 else None
		if selected_property:
			yn = askyesno('Media Processor Configurator | Confirm', f'Are you sure you want to delete "{selected_property}"?')
			if yn:
				command(self.lconn, [f'remove property "{selected_property}"', f'remove setting "{selected_property}"', 'commit'])
				self.update_properties_list()

	def remove_selected_destination(self) -> None:
		selected_destination: Optional[str] = self.destination_listbox.get(self.destination_listbox.curselection()[0]) if len(self.destination_listbox.curselection()) > 0 else None
		if selected_destination:
			yn = askyesno('Media Processor Configurator | Confirm', f'Are you sure you want to delete "{selected_destination}"?')
			if yn:
				command(self.lconn, [f'remove destination "{selected_destination}"', 'commit'])
				self.update_destinations_list()

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
		Label(settings_frame, text='FFMPEG Input Args:').grid(row=1, column=0)
		self.ffmpeg_input_args_entry = Entry(settings_frame)
		self.ffmpeg_input_args_entry.grid(row=1, column=1)
		Label(settings_frame, text='FFMPEG Output Args:').grid(row=2, column=0)
		self.ffmpeg_output_args_entry = Entry(settings_frame)
		self.ffmpeg_output_args_entry.grid(row=2, column=1)
		Label(settings_frame, text='Output Container:').grid(row=3, column=0)
		self.output_container_entry = Entry(settings_frame)
		self.output_container_entry.grid(row=3, column=1)
		Label(settings_frame, text='Destination Server (leave blank for local):').grid(row=4, column=0)
		with self.root_window.lconn:
			self.root_window.lconn.cur.execute('''SELECT user_at_ip FROM destination_servers;''')
			user_at_ips = list(map(lambda uai: uai[0], self.root_window.lconn.cur.fetchall()))
		self.destination_server_box = ttk.Combobox(settings_frame, values=user_at_ips)
		self.destination_server_box.grid(row=4, column=1)
		Label(settings_frame, text='Folder:').grid(row=5, column=0)
		self.folder_entry = Entry(settings_frame)
		self.folder_entry.grid(row=5, column=1)
		self.is_show_var = IntVar()
		is_show_checkbox = Checkbutton(settings_frame, text='Is Show?', variable=self.is_show_var)
		is_show_checkbox.grid(row=6, column=0, columnspan=2)
		Label(settings_frame, text='Season Override (leave blank for auto):').grid(row=7, column=0)
		self.season_override_entry = Entry(settings_frame)
		self.season_override_entry.grid(row=7, column=1)

		action_frame = Frame(self.add_edit_window)
		action_frame.grid(row=4, column=0, sticky=SE)
		Button(action_frame, text='Save and Exit', command=self.save_and_exit).grid(row=0, column=0, padx=5)

		selected_property: Optional[str] = self.root_window.property_listbox.get(self.root_window.property_listbox.curselection()[0]) if len(self.root_window.property_listbox.curselection()) > 0 else None
		if selected_property:
			prop = get_properties(self.root_window.lconn, selected_property)
			settings = get_property_settings(self.root_window.lconn, selected_property)
			if prop:
				self.property_entry.insert(0, prop[0])
				self.pattern_entry.insert(0, prop[1])
				self.partial_var.set(prop[2])
			if settings:
				self.ffmpeg_input_args_entry.insert(0, settings[1])
				self.ffmpeg_output_args_entry.insert(0, settings[2])
				self.output_container_entry.insert(0, settings[3])
				self.destination_server_box.set(settings[3] if settings[4] else '')
				self.folder_entry.insert(0, settings[5])
				self.is_show_var.set(settings[6])
				self.season_override_entry.insert(0, settings[7])

	def get_values(self) -> dict:
		'''Get the values as a dict of lists representing the DB entries'''
		prop = self.property_entry.get()
		return {
			'properties': [
				prop,
				self.pattern_entry.get(),
				str(self.partial_var.get())
			],
			'settings': [
				prop,
				self.ffmpeg_input_args_entry.get(),
				self.ffmpeg_output_args_entry.get(),
				self.output_container_entry.get(),
				self.folder_entry.get(),
				self.destination_server_box.get(),
				str(self.is_show_var.get()),
				self.season_override_entry.get()
			]
		}

	def save_and_exit(self) -> None:
		'''Save changes and close TopLevel'''
		values = self.get_values()
		command(self.root_window.lconn, [
			'add property "' + '" "'.join(values['properties']) + '"',
			'add setting "' +  '"  "'.join(values['settings']) + '"',
			'commit'
		])
		self.root_window.update_properties_list()
		self.add_edit_window.destroy()
	

class AddEditDestinationWindow:
	def __init__(self, root_window: RootWindow) -> None:
		self.root_window = root_window

		# Build window
		self.add_edit_window = Toplevel()
		self.add_edit_window.minsize(500, 500)
		self.add_edit_window.title('Media Processor Configurator | Add Edit Destination')
		self.add_edit_window.grid_columnconfigure(0, weight=1)
		self.add_edit_window.grid_rowconfigure(0, weight=1)

		main_frame = Frame(self.add_edit_window)
		main_frame.grid(row=0, column=0, sticky=N)

		destination_frame = Frame(main_frame)
		destination_frame.grid(row=0, column=0, pady=10)
		Label(destination_frame, text='Destination').grid(row=0, column=0, columnspan=2)
		Label(destination_frame, text='user@ip[:port]:').grid(row=1, column=0)
		self.user_at_ip_entry = Entry(destination_frame)
		self.user_at_ip_entry.grid(row=1, column=1)
		Label(destination_frame, text='Password (UNENCRYPTED!) (optional if using ssh keys):').grid(row=2, column=0)
		self.password_entry = Entry(destination_frame, show='*')
		self.password_entry.grid(row=2, column=1)

		action_frame = Frame(self.add_edit_window)
		action_frame.grid(row=1, column=0, sticky=SE)
		Button(action_frame, text='Save and Exit', command=self.save_and_exit).grid(row=0, column=0, padx=5)

		selected_destination: Optional[str] = self.root_window.destination_listbox.get(self.root_window.destination_listbox.curselection()[0]) if len(self.root_window.destination_listbox.curselection()) > 0 else None
		if selected_destination:
			destination = get_destinations(self.root_window.lconn, selected_destination)
			if destination:
				self.user_at_ip_entry.insert(0, destination[0])
				self.password_entry.insert(0, destination[1])

	def get_values(self) -> dict:
		'''Get the values as list representing the DB entry'''
		return [
			self.user_at_ip_entry.get(),
			self.password_entry.get()
		]

	def save_and_exit(self) -> None:
		'''Save changes and close TopLevel'''
		values = self.get_values()
		command(self.root_window.lconn, [
			'add destination "' + '" "'.join(values) + '"',
			'commit'
		])
		self.root_window.update_destinations_list()
		self.add_edit_window.destroy()


def driver(lconn: LockableSqliteConn) -> None:
	RootWindow(lconn)