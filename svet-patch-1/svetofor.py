import tkinter as tk
from tkinter import simpledialog, messagebox, PhotoImage
import time
from PIL import Image, ImageTk
import random

# 👩‍💼 Сергей (тимлид) — начало
# Создаем главное окно
root = tk.Tk()
root.title("Симуляция светофора")

# Устанавливаем окно на полный экран
root.state('zoomed')
root.resizable(False, False)  # Запрещаем изменение размера окна

# Основная рамка для размещения всех элементов
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

# Создаем панель меню слева
menu_frame = tk.Frame(main_frame, bg="lightgrey", width=200)
menu_frame.pack(side="left", fill="y")
# 👩‍💼 Сергей (тимлид) — конец

# 🧪 Дина (инженер тестировщик) — начало
# Переменные для таймера и состояния светофора
pedestrian_light_state = "red"
driver_light_state = "green"
timer_value = 0
timer_text_id = None
waiting_for_green = False
timer_running = False
green_duration = 25
red_duration = 20
simulation_started = False
last_update_time = 0

# Переменные для машин
cars = []
car_images = []
car_speed = 21  # пикселей за кадр
car_spawn_interval = 1  # секунды между появлением новых машин
last_car_spawn_time = 0

# Переменные для пешеходов
pedestrians = []
pedestrian_spawn_interval = 5  # секунды между появлением новых пешеходов
last_pedestrian_spawn_time = 0
max_pedestrians = 7  # Максимальное количество пешеходов
# 🧪 Дина (инженер тестировщик) — конец

# 👨‍🎓 Иван Рыков — начало
# Загрузка изображений машин
for i in range(1, 5):
    image = Image.open(f"assets/cars/car{i}.png")
    image = image.resize((200, 100), Image.LANCZOS)
    car_images.append(ImageTk.PhotoImage(image))
    flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
    car_images.append(ImageTk.PhotoImage(flipped_image))
# 👨‍🎓 Иван Рыков — конец


# 👨‍💻 Марсель — начало
class Car:
    def __init__(self, canvas, x, y, direction, image):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.direction = direction
        self.image = image
        self.id = canvas.create_image(x, y, image=image, anchor="nw", tags="car")
        self.stopped = False

    def move(self):
        if not self.stopped:
            if self.direction == "left":
                self.x -= car_speed
            else:
                self.x += car_speed
            self.canvas.move(self.id, -car_speed if self.direction == "left" else car_speed, 0)

    def stop(self):
        self.stopped = True

    def resume(self):
        self.stopped = False

    def is_at_stop_line(self):
        canvas_width = self.canvas.winfo_width()
        if self.direction == "left":
            stop_line_x = canvas_width // 2 + 225
            return self.x <= stop_line_x
        else:
            stop_line_x = canvas_width // 2 - 170
            return self.x + 250 >= stop_line_x

    def is_past_stop_line(self):
        canvas_width = self.canvas.winfo_width()
        if self.direction == "left":
            stop_line_x = canvas_width // 2 + 180
            return self.x + 250 < stop_line_x
        else:
            stop_line_x = canvas_width // 2 - 180
            return self.x > stop_line_x

    def is_off_screen(self):
        canvas_width = self.canvas.winfo_width()
        return self.x + 250 < 0 or self.x > canvas_width

    def is_on_crosswalk(self):
        canvas_width = self.canvas.winfo_width()
        crosswalk_start = canvas_width // 2 - 130
        crosswalk_end = canvas_width // 2 + 150
        return crosswalk_start <= self.x <= crosswalk_end or crosswalk_start <= self.x + 250 <= crosswalk_end

    def is_near_pedestrian(self, pedestrians):
        for pedestrian in pedestrians:
            if self.direction == "left":
                if (self.x - pedestrian.x < 100 and self.x > pedestrian.x) and abs(self.y - pedestrian.y) < 50:
                    return True
            else:
                if (pedestrian.x - (self.x + 250) < 100 and self.x < pedestrian.x) and abs(self.y - pedestrian.y) < 50:
                    return True
        return False
# 👨‍💻 Марсель — конец


# 👩‍🎓 Аня — начало(поведение людей)
class Pedestrian:
    def __init__(self, canvas, image_path, x, y):
        self.canvas = canvas
        self.sprite = PhotoImage(file=image_path).subsample(10, 10)
        self.id = canvas.create_image(x, y, image=self.sprite, tags="pedestrian")

        # Позиция и движение
        self.x, self.y = x, y
        self.crosswalk_center_y = canvas.winfo_height() // 2
        self.target_y = self.crosswalk_center_y + road_height // 2 + 1

        self.base_speed = 2
        self.current_speed = self.base_speed
        self.crossing_speed = self.base_speed
        self.acceleration = 0.1
        self.x_shift = random.uniform(-0.05, 0.05)

        # Поведение и ограничения
        self.relaxed_speed = self.base_speed * 0.7
        self.hurry_threshold = 5
        self.state = "walking_to_crosswalk"
                # Ширина тротуара — от левого края до правого края, но с отступом от забора
        self.min_x = 80  # отступ от левого края
        self.max_x = canvas.winfo_width() - 80  # отступ от правого края
                # Координаты тротуара (примерные)
        trotoar_left = 0
        trotoar_right = canvas.winfo_width()

        # Добавляем небольшие отступы от краёв (чтобы не прижимались к деревьям)
        self.min_x = trotoar_left - 1000
        self.max_x = trotoar_right - 700

    def move(self):
        global timer_value, pedestrian_light_state
        
        # === Идёт к переходу ===
        if self.state == "walking_to_crosswalk":
            if self.y > self.target_y:
                self.current_speed = min(self.current_speed + self.acceleration, self.base_speed)
                new_x = max(self.min_x, min(self.max_x, self.x + self.x_shift))
                self.canvas.move(self.id, new_x - self.x, -self.current_speed)
                self.x, self.y = new_x, self.y - self.current_speed
            else:
                self.state = "waiting_at_crosswalk"
                self.current_speed = 0

        # === Ждёт зелёного и >5 секунд ===
        elif self.state == "waiting_at_crosswalk":
            if pedestrian_light_state == "green" and timer_value > 7:
                self.state = "crossing_road"
                distance = road_height
                self.crossing_speed = distance / (green_duration * 10)

        # === Переходит ===
        elif self.state == "crossing_road":
            if self.y > self.crosswalk_center_y - road_height // 2:
                if timer_value > self.hurry_threshold:
                    self.current_speed = min(self.current_speed + self.acceleration, self.relaxed_speed)
                else:
                    self.current_speed = min(self.current_speed + self.acceleration * 2, self.crossing_speed * 1.5)
                new_x = max(self.min_x, min(self.max_x, self.x))
                self.canvas.move(self.id, new_x - self.x, -self.current_speed)
                self.x, self.y = new_x, self.y - self.current_speed
            else:
                self.state = "leaving_scene"
                self.current_speed = self.base_speed

        # === Уходит с экрана ===
        elif self.state == "leaving_scene":
            if self.y > 0:
                target_speed = self.base_speed * 0.5
                if self.current_speed > target_speed:
                    self.current_speed = max(self.current_speed - self.acceleration, target_speed)
                new_x = max(self.min_x, min(self.max_x, self.x))
                self.canvas.move(self.id, new_x - self.x, -self.current_speed)
                self.x, self.y = new_x, self.y - self.current_speed
            else:
                # Удаляем с холста и помечаем как завершённого
                self.canvas.delete(self.id)
                self.state = "crossed"

# 👩‍🎓 Аня — конец


# 👩‍🎓 Аня — начало
def load_pedestrian_models(canvas):
    global pedestrians, last_pedestrian_spawn_time
    pedestrians = []
    models = [
        "assets/people/model1.png",
        "assets/people/model2.png",
        "assets/people/model3.png"
    ]
    crosswalk_start = canvas.winfo_width() // 2 - 110
    crosswalk_end = canvas.winfo_width() // 2 + 150
    crosswalk_width = crosswalk_end - crosswalk_start
    spacing = crosswalk_width // (len(models) + 1)

    for i, model in enumerate(models, 1):
        x = crosswalk_start + i * spacing
        y = canvas.winfo_height() + 40 + i * 40
        pedestrian = Pedestrian(canvas, model, x, y)
        pedestrians.append(pedestrian)

    last_pedestrian_spawn_time = time.time()
# 👩‍🎓 Аня — конец


# 👩‍💼 Сергей (тимлид) — начало
# Функции для кнопок
def start_simulation():
    global timer_running, simulation_started, last_update_time, last_car_spawn_time, pedestrians
    if simulation_started:
        return
    timer_running = True
    simulation_started = True
    last_update_time = time.time()
    last_car_spawn_time = time.time()
    load_pedestrian_models(canvas)
    update_lights()
    move_cars()
    spawn_cars()
    spawn_pedestrians()
    print("Симуляция начата")


def pause_simulation():
    global timer_running
    if not simulation_started:
        messagebox.showinfo("Внимание", "Необходимо начать симуляцию")
        return
    timer_running = False
    print("Симуляция приостановлена")


def resume_simulation():
    global timer_running, last_update_time
    if not simulation_started:
        messagebox.showinfo("Внимание", "Необходимо начать симуляцию")
        return
    if timer_running:
        return
    timer_running = True
    last_update_time = time.time()
    update_lights()
    move_cars()
    spawn_cars()
    spawn_pedestrians()
    print("Симуляция продолжается")


def stop_simulation():
    global timer_running, pedestrian_light_state, driver_light_state, timer_value, waiting_for_green, simulation_started, cars, pedestrians
    timer_running = False
    simulation_started = False
    pedestrian_light_state = "red"
    driver_light_state = "green"
    timer_value = 0
    waiting_for_green = False
    update_lights()
    for car in cars:
        canvas.delete(car.id)
    cars = []
    for pedestrian in pedestrians:
        canvas.delete(pedestrian.id)
    pedestrians = []
    print("Симуляция завершена")
# 👩‍💼 Сергей (тимлид) — конец


# 🧪 Дина (инженер тестировщик) — начало
def open_settings():
    global green_duration, red_duration
    settings_window = tk.Toplevel(root)
    settings_window.title("Настройки")

    tk.Label(settings_window, text="Длительность зеленого сигнала (в секундах):").grid(row=0, column=0, padx=5, pady=5)
    green_entry = tk.Entry(settings_window)
    green_entry.insert(0, str(green_duration))
    green_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(settings_window, text="Длительность красного сигнала (в секундах):").grid(row=1, column=0, padx=5, pady=5)
    red_entry = tk.Entry(settings_window)
    red_entry.insert(0, str(red_duration))
    red_entry.grid(row=1, column=1, padx=5, pady=5)

    def save_settings():
        global green_duration, red_duration
        try:
            new_green_duration = int(green_entry.get())
            new_red_duration = int(red_entry.get())
            if new_green_duration <= 0 or new_red_duration <= 0:
                raise ValueError("Значения должны быть положительными")
            green_duration = new_green_duration
            red_duration = new_red_duration
            for pedestrian in pedestrians:
                if pedestrian.state == "crossing_road":
                    distance_to_cross = road_height
                    pedestrian.speed = distance_to_cross / (green_duration * 10)
            settings_window.destroy()
            messagebox.showinfo("Настройки сохранены",
                                "Для применения новых настроек необходимо перезапустить симуляцию")
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите положительные целые числа (отличные от нуля)")

    tk.Button(settings_window, text="Сохранить", command=save_settings).grid(row=2, column=0, columnspan=2, pady=10)
# 🧪 Дина (инженер тестировщик) — конец

def exit_application():
    if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
        root.quit()

# 👩‍💻 Дарья Лексина — начало
# Кнопки в меню
buttons = {
    "Начать симуляцию": start_simulation,
    "Закончить симуляцию": stop_simulation,
    "Выход": exit_application,
}

# Создаем и размещаем кнопки
for btn_text, func in buttons.items():
    button = tk.Button(menu_frame, text=btn_text, command=func, font=("Arial", 15), height=3, width=20)
    button.pack(pady=5)
# 👩‍💻 Дарья Лексина — конец

# 👨‍💻 Никита Лаптев — начало
# Поле для симуляции
canvas = tk.Canvas(main_frame, bg="white")
canvas.pack(side="right", fill="both", expand=True)

# Загрузка фонового изображения
background_image = Image.open("assets/bg/fon.png")
background_photo = ImageTk.PhotoImage(background_image)
# 👨‍💻 Никита Лаптев — конец


# 👨‍💻 Никита Лаптев — начало
# Создаем разметку дороги и перехода
def draw_road():
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    canvas.create_image(0, 0, anchor="nw", image=background_photo, tags="background")

    road_y = canvas_height // 2
    global road_height
    road_height = 350
    canvas.create_rectangle(0, road_y - road_height // 2, canvas_width, road_y + road_height // 2, fill="gray",
                            tags="road")
    canvas.create_line(0, road_y, canvas_width, road_y, fill="white", dash=(20, 10), tags="road")


def draw_crosswalk():
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    crosswalk_x = canvas_width // 2 - 130
    crosswalk_width = 280
    crosswalk_start_y = canvas_height // 2 - road_height // 2
    crosswalk_end_y = canvas_height // 2 + road_height // 2

    y = crosswalk_start_y
    while y < crosswalk_end_y:
        # Чёрная полоса
        canvas.create_rectangle(crosswalk_x, y, crosswalk_x + crosswalk_width, min(y + 30, crosswalk_end_y),
                                fill="black", tags="crosswalk")
        y += 30
        if y < crosswalk_end_y:
            # Белая полоса
            canvas.create_rectangle(crosswalk_x, y, crosswalk_x + crosswalk_width, min(y + 30, crosswalk_end_y),
                                    fill="white", tags="crosswalk")
            y += 30

    stop_line_offset = 50
    left_stop_line_x = crosswalk_x - stop_line_offset
    right_stop_line_x = crosswalk_x + crosswalk_width + stop_line_offset
    canvas.create_line(left_stop_line_x, canvas_height // 2, left_stop_line_x, crosswalk_end_y, fill="white",
                       width=5, tags="stop_line")
    canvas.create_line(right_stop_line_x, crosswalk_start_y, right_stop_line_x, canvas_height // 2, fill="white",
                       width=5, tags="stop_line")
# 👨‍💻 Никита Лаптев — конец


# 👩‍🎓 Аня — начало
def start_pedestrian_timer():
    global pedestrian_light_state, timer_value, waiting_for_green, timer_running
    if not simulation_started:
        messagebox.showinfo("Внимание", "Необходимо начать симуляцию")
        return
    if not timer_running:
        messagebox.showinfo("Внимание", "Необходимо продолжить симуляцию или начать заново")
        return
    if pedestrian_light_state == "red" and not waiting_for_green and timer_running:
        waiting_for_green = True
        timer_value = red_duration
        update_lights()
# 👩‍🎓 Аня — конец


# 👨‍💻 Никита Кочнев — начало
def update_lights():
    global timer_value, pedestrian_light_state, driver_light_state
    global timer_text_id, waiting_for_green, timer_running, last_update_time

    # Удаляем старые элементы светофоров
    canvas.delete("driver_light", "pedestrian_light")

    now = time.time()
    delta = now - last_update_time
    last_update_time = now

    # === Обработка состояния пешеходного светофора ===
    if pedestrian_light_state == "red":
        # Красный сигнал для пешеходов (верхний)
        canvas.create_oval(
            pedestrian_light_x + 5, pedestrian_light_y + 5,
            pedestrian_light_x + 40, pedestrian_light_y + 40,
            fill="red", tags="pedestrian_light"
        )

        if timer_running and waiting_for_green:
            timer_value -= delta

            # Переходный этап — желтый свет для водителей
            if timer_value <= 3 and driver_light_state != "yellow":
                driver_light_state = "yellow"

            # Смена сигналов при истечении таймера
            if timer_value <= 0:
                pedestrian_light_state, driver_light_state = "green", "red"
                timer_value = green_duration

                # Перерисовываем светофор для пешехода (зеленый в нижнем положении)
                canvas.delete("pedestrian_light") # Удаляем предыдущий
                canvas.create_oval(
                    pedestrian_light_x + 5, pedestrian_light_y + 60, # <-- ИСПРАВЛЕНО: +5, +60
                    pedestrian_light_x + 40, pedestrian_light_y + 95,
                    fill="green", tags="pedestrian_light"
                )

    else:
        # Зелёный сигнал для пешеходов (нижний)
        canvas.create_oval(
            pedestrian_light_x + 5, pedestrian_light_y + 60, # <-- ИСПРАВЛЕНО: +5, +60
            pedestrian_light_x + 40, pedestrian_light_y + 95,
            fill="green", tags="pedestrian_light"
        )

        if timer_running:
            timer_value -= delta

            # Возврат в исходное состояние
            if timer_value <= 0:
                pedestrian_light_state, driver_light_state = "red", "green"
                timer_value = 0
                waiting_for_green = False

    # === Обновление сигналов для водителей ===
    draw_driver_lights()

    # === Обновление движения пешеходов ===
    for person in pedestrians:
        if pedestrian_light_state == "green" and person.y <= person.target_y:
            person.waiting = False
        person.move()

    # Удаляем завершивших переход
    pedestrians[:] = [p for p in pedestrians if p.state != "crossed"]


# 👩‍💻 Дарья Лексина — начало
    if timer_running or pedestrian_light_state == "green":
        color = "green" if pedestrian_light_state == "green" else "red"
        if timer_text_id is None:
            timer_text_id = canvas.create_text(pedestrian_light_x + 75, pedestrian_light_y + 25,
                                               text=f"{timer_value:.1f}", font=("Arial", 16), fill=color, tags="timer")
        else:
            canvas.itemconfigure(timer_text_id, text=f"{timer_value:.1f}", fill=color)
    else:
        if timer_text_id is not None:
            canvas.itemconfigure(timer_text_id, text=f"{timer_value:.1f}")
# 👩‍💻 Дарья Лексина — конец


# 👨‍💻 Никита Кочнев — начало
    if timer_running:
        # Продолжаем обновление цикла через 100 мс
        canvas.after(100, update_lights)
    else:
        # Приостановка таймера — обновляем визуальное состояние
        draw_driver_lights()

        ped_x, ped_y = pedestrian_light_x, pedestrian_light_y
        red_area = (ped_x + 5, ped_y + 5, ped_x + 40, ped_y + 40)
        green_area = (ped_x + 115, ped_y + 5, ped_x + 150, ped_y + 40)

        # Рисуем сигналы пешеходного светофора в зависимости от состояния
        if pedestrian_light_state == "red":
            canvas.create_oval(*red_area, fill="red", tags="pedestrian_light")
            canvas.create_oval(*green_area, fill="black", tags="pedestrian_light")
        else:
            canvas.create_oval(*red_area, fill="black", tags="pedestrian_light")
            canvas.create_oval(*green_area, fill="green", tags="pedestrian_light")
# 👨‍💻 Никита Кочнев — конец


# 👨‍💻 Никита Лаптев — начало
    # Устанавливаем порядок слоев
    canvas.tag_raise("traffic_light")
    canvas.tag_raise("timer")
    canvas.tag_raise("pedestrian_light")
    canvas.tag_raise("driver_light")
# 👨‍💻 Никита Лаптев — конец


# 👩‍💻 Дарья Лексина — начало
# Добавляем кнопку для пешеходного светофора
button_frame = tk.Frame(menu_frame)
button_frame.pack(pady=20)

pedestrian_button = tk.Button(
    button_frame,
    text="Включить пешеходный светофор",
    command=start_pedestrian_timer,
    width=28,
    height=2,
    bg="#ccffcc",
    font=("Arial", 11, "bold")
)
pedestrian_button.pack()
# 👩‍💻 Дарья Лексина — конец


# 👨‍💻 Никита Лаптев — начало
# Функция для отрисовки светофоров
def draw_traffic_lights():
    global pedestrian_light_x, pedestrian_light_y, driver_light_x_left, driver_light_x_right, driver_light_y

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    driver_light_y = canvas_height // 2 - 40
    line_y = canvas_height // 2
    driver_light_x_left = canvas_width // 2 - 170
    driver_light_x_right = canvas_width // 2 + 160

    canvas.create_rectangle(driver_light_x_left, driver_light_y, driver_light_x_left + 30, driver_light_y + 90,
                            fill="black", tags="traffic_light")
    canvas.create_rectangle(driver_light_x_right, driver_light_y, driver_light_x_right + 30, driver_light_y + 90,
                            fill="black", tags="traffic_light")

      # Пешеходный светофор — вертикально, слева от дороги
    pedestrian_light_x = canvas_width // 2 - 300  # Сдвинули влево — на тротуар
    pedestrian_light_y = line_y - 250  # Сдвинули вверх — выше дороги
    canvas.create_rectangle(pedestrian_light_x, pedestrian_light_y, pedestrian_light_x + 45, pedestrian_light_y + 100,
                            fill="black", tags="traffic_light")

    # Красный сигнал — сверху
    canvas.create_oval(pedestrian_light_x + 5, pedestrian_light_y + 5, 
                       pedestrian_light_x + 40, pedestrian_light_y + 40, 
                       fill="red", tags="pedestrian_red")

    # Зелёный сигнал — снизу
    canvas.create_oval(pedestrian_light_x + 5, pedestrian_light_y + 60, 
                       pedestrian_light_x + 40, pedestrian_light_y + 95, 
                       fill="black", tags="pedestrian_green")
    draw_driver_lights()


def draw_driver_lights():
    for x in [driver_light_x_left, driver_light_x_right]:
        canvas.create_oval(x + 5, driver_light_y + 5, x + 25, driver_light_y + 25,
                           fill="red" if driver_light_state == "red" else "black", tags="driver_light")
        canvas.create_oval(x + 5, driver_light_y + 35, x + 25, driver_light_y + 55,
                           fill="yellow" if driver_light_state == "yellow" else "black", tags="driver_light")
        canvas.create_oval(x + 5, driver_light_y + 65, x + 25, driver_light_y + 85,
                           fill="green" if driver_light_state == "green" else "black", tags="driver_light")
# 👨‍💻 Никита Лаптев — конец


# 👨‍💻 Никита Лаптев — начало
# Функция для обновления размеров при изменении размера окна
def update_canvas(event):
    canvas.delete("all")

    global background_photo
    resized_background = background_image.resize((event.width, event.height), Image.LANCZOS)
    background_photo = ImageTk.PhotoImage(resized_background)

    draw_road()
    draw_crosswalk()
    draw_traffic_lights()
    if simulation_started:
        load_pedestrian_models(canvas)

    canvas.tag_raise("background")
    canvas.tag_raise("road")
    canvas.tag_raise("stop_line")
    canvas.tag_raise("crosswalk")
    canvas.tag_raise("pedestrian")
    canvas.tag_raise("car")
    canvas.tag_raise("traffic_light")
    canvas.tag_raise("timer")
    canvas.tag_raise("pedestrian_light")
    canvas.tag_raise("driver_light")
# 👨‍💻 Никита Лаптев — конец


# 👨‍💻 Никита Лаптев — начало
# Привязываем функцию обновления к изменению размеров окна
canvas.bind("<Configure>", update_canvas)
# 👨‍💻 Никита Лаптев — конец


# 👨‍💻 Никита Кочнев — начало
def spawn_cars():
    global last_car_spawn_time

    # Проверяем активность симуляции и таймера
    if not (simulation_started and timer_running):
        return

    now = time.time()
    time_gap = now - last_car_spawn_time

    # Проверяем интервал появления машин
    if time_gap >= car_spawn_interval:
        w, h = canvas.winfo_width(), canvas.winfo_height()

        # === Спавн машин, движущихся влево ===
        left_side_cars = [c for c in cars if c.direction == "left"]
        if len(left_side_cars) < 3:
            idx = random.randrange(0, len(car_images) // 2) * 2 + 1
            y_pos = h // 2 - 125
            new_left_car = Car(canvas, w, y_pos, "left", car_images[idx])
            cars.append(new_left_car)

        # === Спавн машин, движущихся вправо ===
        right_side_cars = [c for c in cars if c.direction == "right"]
        if len(right_side_cars) < 3:
            idx = random.randrange(0, len(car_images) // 2) * 2
            y_pos = h // 2 + 50
            new_right_car = Car(canvas, -250, y_pos, "right", car_images[idx])
            cars.append(new_right_car)

        # Обновляем время последнего спавна
        last_car_spawn_time = now

    # Продолжаем цикл спавна, если таймер активен
    if timer_running:
        canvas.after(1000, spawn_cars)
# 👨‍💻 Никита Кочнев — конец


# 👨‍🎓 Иван Рыков — начало
def spawn_pedestrians():
    global last_pedestrian_spawn_time, pedestrians
    if not simulation_started or not timer_running:
        return

    current_time = time.time()
    if current_time - last_pedestrian_spawn_time >= pedestrian_spawn_interval and len(pedestrians) < max_pedestrians:
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        models = [
            "assets/people/model1.png",
            "assets/people/model2.png",
            "assets/people/model3.png"
        ]
        crosswalk_start = canvas_width // 2 - 130
        crosswalk_end = canvas_width // 2 + 150

        x = random.randint(crosswalk_start, crosswalk_end)
        y = canvas_height + 50

        model = random.choice(models)
        new_pedestrian = Pedestrian(canvas, model, x, y)
        pedestrians.append(new_pedestrian)

        last_pedestrian_spawn_time = current_time

    if timer_running:
        canvas.after(1000, spawn_pedestrians)
# 👨‍🎓 Иван Рыков — конец


# 👨‍💻 Марсель — начало
def move_cars():
    if not simulation_started or not timer_running:
        return

    for car in cars:
        if car.is_near_pedestrian(pedestrians):
            car.stop()
            continue
            
        car_should_stop = False
        for other_car in cars:
            if car != other_car and car.direction == other_car.direction:
                if car.direction == "left":
                    if other_car.x < car.x and car.x - (other_car.x + 150) < 100:
                        car_should_stop = True
                        break
                else:  
                    if other_car.x > car.x and other_car.x - (car.x + 150) < 100:
                        car_should_stop = True
                        break
        
        if car_should_stop:
            car.stop()
            continue
            
        if not car.is_on_crosswalk():
            if driver_light_state in ["red", "yellow"] and car.is_at_stop_line() and not car.is_past_stop_line():
                car.stop()
            else:
                car.resume()
        else:
            car.resume()

        car.move()

    cars[:] = [car for car in cars if not car.is_off_screen()]

    if timer_running:
        canvas.after(50, move_cars)
# 👨‍💻 Марсель — конец


# 👩‍💼 Сергей (тимлид) — начало
# Рисуем все элементы
draw_road()
draw_crosswalk()
draw_traffic_lights()

# Запускаем основной цикл приложения
root.mainloop()
# 👩‍💼 Сергей (тимлид) — конец
