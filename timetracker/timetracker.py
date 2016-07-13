import tkinter as tk
from tkinter import messagebox

from models import session, Project, Task, TimeEntry


class Application(tk.Frame):
    projects = {}
    timer_buttons = {}
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
        self.main_screen = tk.Frame(height=2, bd=1)
        self.main_screen.pack(padx=5, pady=5)
        main_label = tk.Label(self.main_screen, text="Projects", font="default 16 bold")
        main_label.pack(side='top')
        self.update_projects_list()
        b = tk.Button(self.main_screen, text="Create A New Project", command=self.show_new_project_popup)
        b.pack(side='bottom')

    def update_projects_list(self):
        for project in session.query(Project).all():
            if not self.projects.get(project.id, None):
                self.projects[project.id] = tk.Label(self.main_screen, text=project.name, fg="black")
                self.projects[project.id].pack(side='top')
                self.projects[project.id].bind(
                    "<Button-1>", lambda event, project_id=project.id: self.open_project_screen(event, project_id)
                )

    def reset_projects_list(self):
        self.projects = {}
        self.update_projects_list()

    def show_new_project_popup(self):
        self.popup = tk.Toplevel()
        self.popup.title("Create A New Project")
        self.project_name_input = tk.Entry(self.popup)
        self.project_name_input.delete(0, tk.END)
        self.project_name_input.insert(0, "Project Name...")
        self.project_name_input.pack()
        create_button = tk.Button(self.popup, text="Create", command=self.create_new_project)
        create_button.pack(side='left')
        close_button = tk.Button(self.popup, text="Close", command=self.popup.destroy)
        close_button.pack(side='right')

    def update_tasks_list(self, project_id):
        tasks = session.query(Task).filter_by(project_id=project_id)
        num_tasks = tasks.count()
        rows = 1
        if tasks.count() == 0:
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
                                  command=lambda: self.show_new_task_popup(project_id))
        create_button.grid(row=(rows + 1), columnspan=2)

        delete_button = tk.Button(
            self.project_screen, text="Delete",
            command=lambda project_id=project_id: self.show_delete_project_dialog(project_id)
        )
        delete_button.grid(row=(rows + 2), column=0)

        back_button = tk.Button(self.project_screen, text="Back", command=self.back_to_main_screen)
        back_button.grid(row=(rows + 2), column=1)

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

        self.open_main_screen()
        self.reset_projects_list()

    def open_project_screen(self, event, project_id):
        self.refresh_project_screen(project_id)

    def show_new_task_popup(self, project_id):
        self.popup = tk.Toplevel(padx=5, pady=5)
        self.popup.title("Create A New Task")
        task_name_label = tk.Label(self.popup, text='Task Name:')
        task_name_label.grid(row=0, columnspan=2, stick=tk.W)
        self.task_name_input = tk.Entry(self.popup, width=25)
        self.task_name_input.delete(0, tk.END)
        self.task_name_input.grid(row=1, columnspan=2, stick=tk.W)
        task_external_id_label = tk.Label(self.popup, text='Task ID in external tracker:')
        task_external_id_label.grid(row=2, columnspan=2, stick=tk.W)
        task_external_id_input = tk.Entry(self.popup, width=25)
        task_external_id_input.delete(0, tk.END)
        task_external_id_input.grid(row=3, columnspan=4, stick=tk.W)
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
            self.refresh_main_screen()
            self.back_to_main_screen()

    def open_task_popup(self, event, task_id):
        self.popup = tk.Toplevel()
        self.popup.title("Logged time")
        task_label = tk.Label(self.popup, text="Logged time for task #%s" % task_id, font="default 16 bold")
        task_label.pack(side='top')
        logs = session.query(TimeEntry).filter_by(task_id=task_id)
        if logs.count() == 0:
            no_logs_label = tk.Label(self.popup, text="No logs found.")
            no_logs_label.pack(side='top')
        else:
            for log in logs:
                start_dt = getattr(log, 'start_datetime', '')
                if start_dt:
                    start_dt = start_dt.strftime('%d.%m.%y %H:%M')
                end_dt = getattr(log, 'end_datetime', '')
                if end_dt is not None:
                    end_dt = end_dt.strftime('%d.%m.%y %H:%M')
                else:
                    end_dt = '...'
                label = tk.Label(self.popup, text='%s - %s' % (start_dt, end_dt))
                label.pack(side='bottom', anchor=tk.W)

    def create_new_project(self):
        Project.create_project(name=self.project_name_input.get())
        self.update_projects_list()
        self.popup.destroy()

    def create_new_task(self, project_id):
        Task.create_task(name=self.task_name_input.get(), project_id=project_id)
        self.update_tasks_list(project_id)
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
