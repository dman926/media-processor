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

def add_edit_property(lconn: LockableSqliteConn, root: Tk, listbox: Listbox) -> None:
	add_edit_window = Toplevel()
	add_edit_window.minsize(500, 500)
	#add_edit_window.grid_columnconfigure(0, weight=1)
	#add_edit_window.grid_rowconfigure(0, weight=1)

	Label(add_edit_window, text='Property').grid(row=0, column=0, columnspan=2)
	property_entry = Entry(add_edit_window)
	property_entry.grid(row=1, column=1)
	pattern_entry = Entry(add_edit_window)
	pattern_entry.grid(row=2, column=1)
	partial_var = IntVar()
	partial_checkbox = Checkbutton(add_edit_window, text='Partial?', variable=partial_var)
	partial_checkbox.grid(row=3, column=0, columnspan=2)
	Label(add_edit_window, text='Settings').grid(row=4, column=0, columnspan=2)
	ffmpeg_args_entry = Entry(add_edit_window)
	ffmpeg_args_entry.grid(row=5, column=1)
	output_container_entry = Entry(add_edit_window)
	output_container_entry.grid(row=6, column=1)
	folder_entry = Entry(add_edit_window)
	folder_entry.grid(row=7, column=1)
	with lconn:
		lconn.cur.execute('''SELECT user_at_ip FROM destination_servers;''')
		user_at_ips = list(map(lambda uai: uai[0], lconn.cur.fetchall()))
	destination_server_box = ttk.Combobox(add_edit_window, values=user_at_ips)
	destination_server_box.grid(row=8, column=1)
	is_show_var = IntVar()
	is_show_checkbox = Checkbutton(add_edit_window, text='Is Show?', variable=is_show_var)
	is_show_checkbox.grid(row=9, column=0, columnspan=2)
	season_override_entry = Entry(add_edit_window)
	season_override_entry.grid(row=10, column=1)

	selected_property: Optional[str] = listbox.get(listbox.curselection()[0]) if len(listbox.curselection()) > 0 else None
	if selected_property:
		pass
	else:
		pass

def remove_propery(lconn: LockableSqliteConn, root: Tk, listbox: Listbox) -> None:
	pass

def add_edit_destination(lconn: LockableSqliteConn, root: Tk, listbox: Listbox) -> None:
	pass

def remove_destination(lconn: LockableSqliteConn, root: Tk, listbox: Listbox) -> None:
	pass

def quit(root: Tk) -> None:
	print('quit')
	root.quit()

def driver(lconn: LockableSqliteConn) -> None:
	root = Tk()
	root.title('Media Processor Configurator')
	root.minsize(500, 500)
	root.grid_columnconfigure(0, weight=1)
	root.grid_rowconfigure(0, weight=1)

	main_frame = Frame(root)
	main_frame.grid(row=0, column=0, sticky=N)
	
	# Add property listings and action buttons
	property_frame = Frame(main_frame)
	property_frame.grid(row=0, column=0)
	property_listbox = Listbox(property_frame)
	property_listbox.grid(row=0, column=0)
	property_listbox_scroll = Scrollbar(property_frame)
	property_listbox_scroll.grid(row=0, column=1, sticky=N+S+W)
	property_listbox.config(yscrollcommand=property_listbox_scroll.set)
	property_listbox_scroll.config(command=property_listbox.yview)
	property_actions_frame = Frame(main_frame)
	property_actions_frame.grid(row=0, column=1)
	Button(property_actions_frame, text='Add/Edit property', command=lambda: add_edit_property(lconn, root, property_listbox)).grid(row=0, column=0)
	Button(property_actions_frame, text='Remove property', command=lambda: remove_propery(lconn, root, property_listbox)).grid(row=1, column=0)

	for i, row in enumerate(get_properties(lconn)):
		property_listbox.insert(i, row[0])
	
	# Add destination listings and action buttons
	destination_frame = Frame(main_frame)
	destination_frame.grid(row=1, column=0)
	destination_listbox = Listbox(destination_frame)
	destination_listbox.grid(row=0, column=0)
	property_listbox_scroll = Scrollbar(destination_frame)
	property_listbox_scroll.grid(row=0, column=1, sticky=N+S+W)
	property_listbox.config(yscrollcommand=property_listbox_scroll.set)
	property_listbox_scroll.config(command=property_listbox.yview)
	destination_actions_frame = Frame(main_frame)
	destination_actions_frame.grid(row=1, column=1)
	Button(destination_actions_frame, text='Add/Edit destination server', command=lambda: add_edit_destination(lconn, root, property_listbox)).grid(row=0, column=0)
	Button(destination_actions_frame, text='Remove destination server', command=lambda: remove_destination(lconn, root, property_listbox)).grid(row=1, column=0)

	for i, row in enumerate(get_destinations(lconn)):
		destination_listbox.insert(i, row[0])
	
	# Add action button(s)
	action_frame = Frame(root)
	action_frame.grid(row=2, column=0, sticky=SE)
	Button(action_frame, text='Exit', command=lambda: quit(root)).grid(row=0, column=0, padx=5)
	
	root.mainloop()