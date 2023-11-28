import tkinter as tk
from tkinter import ttk
import datetime
import mysql.connector
from tkinter import filedialog, messagebox
from PIL import ImageGrab, Image
from tkinter.filedialog import askopenfilename
import os
import cv2
from numpy import result_type
from skimage.metrics import structural_similarity as ssim

class ESignatureAttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Signature Attendance - Tarlac State University")

        self.background_image = tk.PhotoImage(file="bg-img.png")
        self.background_label = tk.Label(root, image=self.background_image)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Database connection
        self.connection = mysql.connector.connect(host='localhost', user='root', password='')
        if self.connection.is_connected():
            print("Connected to MySQL")

        # Create a cursor to execute SQL queries
        self.cursor = self.connection.cursor()

        # Create 'attendance' database
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS attendance")
        self.cursor.execute("USE attendance")

        # Create 'information' table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS information (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(255) NOT NULL,
                Section VARCHAR(255) NOT NULL,
                Timestamp DATETIME NOT NULL
            )
        """)
        self.connection.commit()

        self.attendance_data = []

        # Layout frames
        self.empty_space = tk.Label(root)
        self.empty_space.pack(pady=15)

        self.text_frame = tk.Frame(root)
        self.text_frame.pack(pady=10)

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=10)

        self.signature_frame = tk.Frame(root)
        self.signature_frame.pack(pady=10)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.button_frame2 = tk.Frame(root)
        self.button_frame2.pack(pady=10)


        text_label = tk.Label(self.text_frame, text="E-Signature Verification Program", font=("Arial", 18))
        text_label.pack()

        # Input fields
        self.name_label = tk.Label(self.input_frame, text="Name:")
        self.name_label.grid(row=0, column=0)
        self.name_entry = tk.Entry(self.input_frame, width=30)
        self.name_entry.grid(row=0, column=1)

        self.section_label = tk.Label(self.input_frame, text="Section:")
        self.section_label.grid(row=1, column=0)
        self.section_entry = tk.Entry(self.input_frame, width=30)
        self.section_entry.grid(row=1, column=1)



        # Signature Canvas
        self.signature_label = tk.Label(self.signature_frame, text="Please sign below to mark your attendance:")
        self.signature_label.pack()
        self.signature_canvas = tk.Canvas(self.signature_frame, width=600, height=300, bg="white")
        self.signature_canvas.pack()

        # Buttons
        self.clear_button = tk.Button(self.button_frame, text="Clear Signature", command=self.clear_signature)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.search_button = tk.Button(self.button_frame, text="Search for your signature", command=self.search_and_open_image)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.button_frame, text="Save Signature", command=self.save_image)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.database_button = tk.Button(self.button_frame2, text="View Database", command=self.view_database)
        self.database_button.pack(side=tk.LEFT, padx=5)

        self.database_button = tk.Button(self.button_frame2, text="Verify Signature", command=self.checkSimilarity)
        self.database_button.pack(side=tk.LEFT, padx=5)

        # Bindings
        self.root.bind("<Button-1>", self.start_signature)
        self.root.bind("<B1-Motion>", self.draw_signature)

    def start_signature(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def draw_signature(self, event):
        x, y = event.x, event.y
        self.signature_canvas.create_line((self.last_x, self.last_y, x, y), fill="black", width=2)
        self.last_x = x
        self.last_y = y

    def clear_signature(self):
        self.signature_canvas.delete("all")

    def save_image(self):
        # Define the destination folder and file name
        name = self.name_entry.get().strip()
        section = self.section_entry.get().strip()
        file_name = self.name_entry.get() + '-' + self.section_entry.get() + '.png'  # Replace with the desired file name and extension
        if name and section:
            # Grab the area of the canvas and save it as an image
            x1 = self.root.winfo_rootx() + self.signature_canvas.winfo_x() + 600
            y1 = self.root.winfo_rooty() + self.signature_canvas.winfo_y() + 300
            x2 = x1 + self.signature_canvas.winfo_width() + 130
            y2 = y1 + self.signature_canvas.winfo_height() + 100
            coordinates = (x1, y1, x2, y2)
            img2 = ImageGrab.grab(bbox=coordinates)
            confirmation = messagebox.askyesno("Confirmation", "Save the signature?")
            if confirmation:
                img2.save(file_name)
                messagebox.showinfo("Signature Save", f"Signature of '{self.name_entry.get()}' have been saved.")
            else:
                messagebox.showinfo("Cancelled", "Signature save cancelled.")
        else:
            messagebox.showinfo("Error", "Name and Section cannot be empty")

    def view_database(self):
        # Fetch and display data from the database in a new window
        self.cursor.execute("SELECT * FROM information")
        data = self.cursor.fetchall()

        if data:
            # Create a new window for displaying database information
            database_window = tk.Toplevel(self.root)
            database_window.title("Database Information")

            # Create Treeview widget
            tree = ttk.Treeview(database_window, columns=("ID", "Name", "Section", "Timestamp"), show="headings")

            # Set column headings
            tree.heading("ID", text="ID")
            tree.heading("Name", text="Name")
            tree.heading("Section", text="Section")
            tree.heading("Timestamp", text="Timestamp")

            # Insert data into Treeview
            for row in data:
                tree.insert("", "end", values=row)

            # Pack the Treeview widget
            tree.pack(expand=True, fill="both")

        else:
            messagebox.showinfo("No data in the 'information' table")



    def checkSimilarity(self):
        THRESHOLD = 90
        name = self.name_entry.get().strip()
        section = self.section_entry.get().strip()
        file_name = self.name_entry.get() + '-' + self.section_entry.get()
        if name and section:
            image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp")  # Image file extensions
            # Check if the file exists with any of the supported extensions
            found_file = None
            for ext in image_extensions:
                full_path = os.path.join(file_name + ext)
                if os.path.isfile(full_path):
                    found_file = full_path
                    break
            if found_file:
                try:
                    x1 = self.root.winfo_rootx() + self.signature_canvas.winfo_x() + 600
                    y1 = self.root.winfo_rooty() + self.signature_canvas.winfo_y() + 300
                    x2 = x1 + self.signature_canvas.winfo_width() + 130
                    y2 = y1 + self.signature_canvas.winfo_height() + 100
                    coordinates = (x1, y1, x2, y2)
                    new_file = ImageGrab.grab(bbox=coordinates)
                    new_file.save('temporary.png')
                    tem_file = os.path.join('temporary.png')

                    img1 = cv2.imread(found_file)
                    img2 = cv2.imread(tem_file)
                    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
                    # resize images for comparison
                    img1 = cv2.resize(img1, (500, 300))
                    img2 = cv2.resize(img2, (500, 300))
                    similarity_value = "{:.2f}".format(ssim(img1, img2) * 100)
                    result = float(similarity_value)
                    if result <= THRESHOLD:
                        messagebox.showerror("Failure: Signatures Do Not Match",
                                             "Signatures are " + str(result) + f" % similar!!")
                        pass
                    else:
                        messagebox.showinfo("Success: Signatures Match",
                                            "Signatures are " + str(result) + f" % similar!!"
                                             "Your Attendance will now be added")
                        name = self.name_entry.get().strip()
                        section = self.section_entry.get().strip()
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # Check if the signature canvas is empty
                        if not self.signature_canvas.find_all():
                            messagebox.showinfo("Error", "Signature cannot be empty")
                            return

                        if name and section:
                            self.attendance_data.append([name, section, timestamp])

                            # Insert data into the database
                            insert_query = "INSERT INTO information (Name, Section, Timestamp) VALUES (%s, %s, %s)"
                            data = (name, section, timestamp)
                            self.cursor.execute(insert_query, data)
                            self.connection.commit()

                            self.name_entry.delete(0, tk.END)
                            self.section_entry.delete(0, tk.END)
                            self.clear_signature()

                            messagebox.showinfo("Success",
                                                f"Attendance submitted for: '{name}' from '{section}' on '{timestamp}'")
                        else:
                            messagebox.showinfo("Error", "Name or section cannot be empty")

                        return True

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open image: {e}")


            else:
                # If no file with supported extensions is found, display a message
                messagebox.showinfo("Signature Not Found", f"Signature of '{file_name}' not found.")
        else:
            messagebox.showinfo("Error", "Name and Section cannot be empty")

    def search_and_open_image(self):
        name = self.name_entry.get().strip()
        section = self.section_entry.get().strip()
        file_name = self.name_entry.get() + self.section_entry.get()
        if name and section:
            image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp")  # Image file extensions
            # Check if the file exists with any of the supported extensions
            found_file = None
            for ext in image_extensions:
                full_path = os.path.join(file_name + ext)
                if os.path.isfile(full_path):
                    found_file = full_path
                    break
            if found_file:
                try:
                    messagebox.showinfo("Signature Found", f"Signature of '{file_name}' found.")
                    img = Image.open(found_file)
                    return img
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open image: {e}")
            else:
                # If no file with supported extensions is found, display a message
                messagebox.showinfo("Signature Not Found", f"Signature of '{file_name}' not found.")
        else:
            messagebox.showinfo("Error", "Name cannot be empty")


def cover_whole_screen(window):
    # Get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Set the window size to cover the whole screen
    window.geometry(f"{screen_width}x{screen_height}+0+0")


if __name__ == "__main__":
    root = tk.Tk()
    cover_whole_screen(root)
    app = ESignatureAttendanceApp(root)
    root.resizable(False, False)
    root.mainloop()