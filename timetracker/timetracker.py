import tkinter as tk
from tkinter import messagebox

from models import session, Project, Task, TimeEntry


class Application(tk.Frame):
    timer_buttons = {}
    main_screen = None
    projects_list_screen = None
    project_screen = None
    popup = None
    project_name_input = None
    task_name_input = None

    def __init__(self, master=None):
        super().__init__(master)
        master.minsize(width=300, height=400)
        self.pack()
        self.open_main_screen()

    def open_main_screen(self):
        self.main_screen = tk.Frame()
        self.main_screen.pack(padx=5, pady=5)
        main_label = tk.Label(self.main_screen, text="Projects", font="default 16 bold")
        main_label.pack(side='top')
        self.update_projects_list()
        b = tk.Button(self.main_screen, text="Create A New Project", command=self.create_or_update_project)
        b.pack(side='bottom')

    def update_projects_list(self):
        if self.projects_list_screen:
            self.projects_list_screen.destroy()
        self.projects_list_screen = tk.Frame(self.main_screen)
        self.projects_list_screen.pack(side='top')
        projects = session.query(Project).all()
        if not projects:
            project_label = tk.Label(self.projects_list_screen, text="No projects found.", fg="black")
            project_label.pack(side='top')
        else:
            for project in session.query(Project).all():
                project_label = tk.Label(self.projects_list_screen, text=project.name, fg="black")
                project_label.pack(side='top')
                project_label.bind(
                    "<Button-1>", lambda event, project_id=project.id: self.open_project_screen(event, project_id)
                )

    def create_or_update_project(self, project_id=None):
        if project_id:
            project = session.query(Project).filter_by(id=project_id).first()
            title = "Edit Project #%s" % project_id
            project_name_placeholder = project.name
        else:
            project_name_placeholder = "Project Name..."
            title = "Create A New Project"
        self.popup = tk.Toplevel()
        self.popup.title(title)
        self.project_name_input = tk.Entry(self.popup)
        self.project_name_input.delete(0, tk.END)
        self.project_name_input.insert(0, project_name_placeholder)
        self.project_name_input.pack()
        if project_id:
            create_button = tk.Button(
                self.popup, text="Save", command=lambda project_id=project_id: self.save_project(project_id)
            )
        else:
            create_button = tk.Button(self.popup, text="Create", command=self.create_new_project)
        create_button.pack(side='left')
        close_button = tk.Button(self.popup, text="Close", command=self.popup.destroy)
        close_button.pack(side='right')

    def update_tasks_list(self, project_id):
        tasks = session.query(Task).filter_by(project_id=project_id)
        num_tasks = tasks.count()
        rows = 1
        if num_tasks == 0:
            no_tasks_label = tk.Label(self.project_screen, text="No tasks found.")
            no_tasks_label.grid(row=1, column=0, columnspan=2)
        else:
            for idx, task in enumerate(tasks):
                row = rows + idx
                task_label = tk.Label(self.project_screen, text=task.name, fg="black")
                task_label.grid(row=row, column=0)
                task_label.bind("<Button-1>", lambda event, task_id=task.id: self.open_task_popup(event, task_id))

                button_params = {}
                if task.is_inprogress:
                    button_params.update(text="Stop", command=lambda task_id=task.id: self.stop_timer(task_id))
                else:
                    button_params.update(text="Start", command=lambda task_id=task.id: self.start_timer(task_id))

                button = tk.Button(self.project_screen, **button_params)
                self.timer_buttons[task.id] = button
                self.timer_buttons[task.id].grid(row=row, column=1)

        rows += num_tasks
        create_button = tk.Button(self.project_screen, text="Create A New Task",
                                  command=lambda: self.show_edit_task_popup(project_id))
        create_button.grid(row=(rows + 1), columnspan=2)

        edit_button = tk.Button(
            self.project_screen, text="Edit",
            command=lambda project_id=project_id: self.create_or_update_project(project_id)
        )
        edit_button.grid(row=(rows + 2), column=0)
        delete_button = tk.Button(
            self.project_screen, text="Delete",
            command=lambda project_id=project_id: self.show_delete_project_dialog(project_id)
        )
        delete_button.grid(row=(rows + 2), column=1)
        back_button = tk.Button(self.project_screen, text="Back", command=self.back_to_main_screen)
        back_button.grid(row=(rows + 3), columnspan=2)

    def refresh_project_screen(self, project_id):
        self.main_screen.pack_forget()
        if self.project_screen:
            self.project_screen.destroy()

        self.project_screen = tk.Frame(height=2, bd=2)
        self.project_screen.pack(padx=5, pady=5)

        task_label = tk.Label(self.project_screen, text="Project #%s" % project_id,
                              font="default 16 bold")
        task_label.grid(row=0, columnspan=2)
        self.update_tasks_list(project_id)

    def refresh_main_screen(self):
        if self.main_screen:
            self.main_screen.destroy()

        self.update_projects_list()
        self.open_main_screen()

    def open_project_screen(self, event, project_id):
        self.refresh_project_screen(project_id)

    def show_edit_task_popup(self, project_id=None, task_id=None):
        if task_id:
            task = session.query(Task).filter_by(id=task_id).first()
            title = "Edit Task #%s" % task_id
        else:
            task = None
            title = "Create A New Task"

        self.popup = tk.Toplevel(padx=5, pady=5)
        self.popup.title(title)
        task_name_label = tk.Label(self.popup, text='Task Name:')
        task_name_label.grid(row=0, columnspan=2, stick=tk.W)
        self.task_name_input = tk.Entry(self.popup, width=25)
        self.task_name_input.delete(0, tk.END)
        if task_id and task and getattr(task, 'name', None):
            self.task_name_input.insert(0, task.name)
        self.task_name_input.grid(row=1, columnspan=2, stick=tk.W)
        external_task_id_label = tk.Label(self.popup, text='Task ID in external tracker:')
        external_task_id_label.grid(row=2, columnspan=2, stick=tk.W)
        self.external_task_id_input = tk.Entry(self.popup, width=25)
        self.external_task_id_input.delete(0, tk.END)
        if task_id and task and getattr(task, 'external_task_id', None):
            self.external_task_id_input.insert(0, task.external_task_id)
        self.external_task_id_input.grid(row=3, columnspan=4, stick=tk.W)
        if task_id:
            create_button = tk.Button(self.popup, text="Save", command=lambda: self.save_task(task_id))
        else:
            create_button = tk.Button(self.popup, text="Create", command=lambda: self.create_new_task(project_id))
        create_button.grid(row=4, column=0)
        close_button = tk.Button(self.popup, text="Close", command=self.popup.destroy)
        close_button.grid(row=4, column=1)

    def show_delete_project_dialog(self, project_id):
        project = session.query(Project).filter_by(id=project_id).first()
        result = messagebox.askquestion('Delete project "%s"' % project.name, 'Are You Sure?', icon='warning')
        if result == 'yes':
            session.delete(project)
            session.commit()
            self.update_projects_list()
            self.back_to_main_screen()

    def open_task_popup(self, event, task_id):
        self.popup = tk.Toplevel(padx=10, pady=10)
        self.popup.title("Task #%s details" % task_id)
        task_label = tk.Label(self.popup, text="Task #%s details" % task_id, font="default 16 bold")
        task_label.grid(row=0, columnspan=2)
        logs = session.query(TimeEntry).filter_by(task_id=task_id)
        num_logs = logs.count()
        if num_logs == 0:
            no_logs_label = tk.Label(self.popup, text="No logs found.")
            no_logs_label.grid(row=1, columnspan=2)
        else:
            for idx, log in enumerate(logs):
                start_dt = getattr(log, 'start_datetime', '')
                if start_dt:
                    start_dt = start_dt.strftime('%d.%m.%y %H:%M:%S')
                end_dt = getattr(log, 'end_datetime', '')
                if end_dt is not None:
                    end_dt = end_dt.strftime('%d.%m.%y %H:%M:%S')
                else:
                    end_dt = '...'
                label = tk.Label(self.popup, text='%s - %s' % (start_dt, end_dt))
                label.grid(row=(idx + 2), columnspan=2)

        edit_button = tk.Button(
            self.popup, text="Edit", command=lambda task_id=task_id: self.show_edit_task_popup(task_id=task_id)
        )
        edit_button.grid(row=(num_logs + 2), column=0)
        delete_button = tk.Button(
            self.popup, text="Delete",
            command=lambda task_id=task_id: self.show_delete_task_dialog(task_id)
        )
        delete_button.grid(row=(num_logs + 2), column=1)

    def create_new_project(self):
        Project.create_project(name=self.project_name_input.get())
        self.update_projects_list()
        self.popup.destroy()

    def save_project(self, project_id):
        project = session.query(Project).filter_by(id=project_id).first()
        project.name = self.project_name_input.get()
        session.commit()
        self.update_projects_list()
        self.popup.destroy()

    def create_new_task(self, project_id):
        Task.create_task(
            name=self.task_name_input.get(), external_task_is=self.external_task_id_input.get(), project_id=project_id
        )
        self.update_tasks_list(project_id)
        self.popup.destroy()
        self.refresh_project_screen(project_id)

    def save_task(self, task_id):
        task = session.query(Task).filter_by(id=task_id).first()
        task.name = self.task_name_input.get()
        task.external_task_id = self.external_task_id_input.get()
        session.commit()
        self.update_tasks_list(task.project_id)
        self.popup.destroy()
        self.refresh_project_screen(task.project_id)

    def show_delete_task_dialog(self, task_id):
        task = session.query(Task).filter_by(id=task_id).first()
        project_id = task.project_id
        result = messagebox.askquestion('Delete task "%s"' % task.name, 'Are You Sure?', icon='warning')
        if result == 'yes':
            session.delete(task)
            session.commit()
            self.popup.destroy()
            self.refresh_project_screen(project_id)

    def start_timer(self, task_id):
        TimeEntry.start_log(task_id=task_id)
        self.timer_buttons[task_id].config(text="Stop", command=lambda: self.stop_timer(task_id))

    def stop_timer(self, task_id):
        TimeEntry.stop_log(task_id=task_id)
        self.timer_buttons[task_id].config(text="Start", command=lambda: self.start_timer(task_id))

    def back_to_main_screen(self):
        self.project_screen.pack_forget()
        self.main_screen.pack()

root = tk.Tk()
root.title("TimeTracker")
app = Application(master=root)
app.mainloop()
