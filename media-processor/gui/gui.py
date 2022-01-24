from tkinter import *
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

def add_edit_property(lconn: LockableSqliteConn, listbox: Listbox) -> None:
	selected_property: Optional[str] = listbox.get(listbox.curselection()[0]) if len(listbox.curselection()) > 0 else None
	if selected_property:
		pass
	else:
		pass

def remove_propery(lconn: LockableSqliteConn, listbox: Listbox) -> None:
	pass

def add_edit_destination(lconn: LockableSqliteConn, listbox: Listbox) -> None:
	pass

def remove_destination(lconn: LockableSqliteConn, listbox: Listbox) -> None:
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
	property_listbox_scroll.grid(row=0, column=1)
	property_listbox.config(yscrollcommand=property_listbox_scroll.set)
	property_listbox_scroll.config(command=property_listbox.yview)
	property_actions_frame = Frame(main_frame)
	property_actions_frame.grid(row=0, column=1)
	Button(property_actions_frame, text='Add/Edit property', command=lambda: add_edit_property(lconn, property_listbox)).grid(row=0, column=0)
	Button(property_actions_frame, text='Remove property', command=lambda: remove_propery(lconn, property_listbox)).grid(row=1, column=0)

	for i, row in enumerate(get_properties(lconn)):
		property_listbox.insert(i, row[0])
	
	# Add destination listings and action buttons
	destination_frame = Frame(main_frame)
	destination_frame.grid(row=1, column=0)
	destination_listbox = Listbox(destination_frame)
	destination_listbox.grid(row=0, column=0)
	property_listbox_scroll = Scrollbar(destination_frame)
	property_listbox_scroll.grid(row=0, column=1)
	property_listbox.config(yscrollcommand=property_listbox_scroll.set)
	property_listbox_scroll.config(command=property_listbox.yview)
	destination_actions_frame = Frame(main_frame)
	destination_actions_frame.grid(row=1, column=1)
	Button(destination_actions_frame, text='Add/Edit destination server', command=lambda: add_edit_destination(lconn, property_listbox)).grid(row=0, column=0)
	Button(destination_actions_frame, text='Remove destination server', command=lambda: remove_destination(lconn, property_listbox)).grid(row=1, column=0)

	for i, row in enumerate(get_destinations(lconn)):
		destination_listbox.insert(i, row[0])
	
	# Add action button(s)
	action_frame = Frame(root)
	action_frame.grid(row=2, column=0, sticky=SE)
	Button(action_frame, text='Exit', command=lambda: quit(root)).grid(row=0, column=0, padx=5)
	
	root.mainloop()