import random
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


class Bed:
    def __init__(self, bed_id):
        self.bed_id = bed_id
        self.is_occupied = False
        self.patient = None
        self.occupied_until = None

    def assign_patient(self, patient, days, current_date):
        self.is_occupied = True
        self.patient = patient
        self.occupied_until = current_date + timedelta(days=days)

    def free_bed(self, current_date):
        if self.is_occupied and self.occupied_until <= current_date:
            message = f"[{current_date.strftime('%Y-%m-%d')}] Пациент {self.patient.patient_id} выписан из койки {self.bed_id}"
            self.is_occupied = False
            self.patient = None
            self.occupied_until = None
            return True, message
        return False, None

    def is_available(self, current_date):
        if self.is_occupied and self.occupied_until <= current_date:
            self.free_bed(current_date)
        return not self.is_occupied


class Department:
    def __init__(self, name, specialties, total_beds):
        self.name = name
        self.specialties = specialties
        self.beds = [Bed(f"{name}_койка_{i + 1}") for i in range(total_beds)]
        self.patients = []
        self.discharged_count = 0

    def get_available_beds(self, current_date):
        return [bed for bed in self.beds if bed.is_available(current_date)]

    def assign_patient(self, patient, current_date):
        available_beds = self.get_available_beds(current_date)
        if available_beds:
            bed = available_beds[0]
            stay_days = random.randint(3, 14)
            bed.assign_patient(patient, stay_days, current_date)
            self.patients.append(patient)
            message = f"[{current_date.strftime('%Y-%m-%d')}] Пациент {patient.patient_id} назначен в {self.name}, койка {bed.bed_id} на {stay_days} дней, диагноз: {patient.diagnosis}"
            return True, message
        return False, None

    def get_occupancy_rate(self, current_date):
        occupied = sum(1 for bed in self.beds if not bed.is_available(current_date))
        return (occupied / len(self.beds)) * 100

    def update_beds(self, current_date):
        messages = []
        for bed in self.beds:
            discharged, message = bed.free_bed(current_date)
            if discharged:
                self.discharged_count += 1
                if message:
                    messages.append(message)
        self.patients = [p for p in self.patients if any(b.patient == p for b in self.beds)]
        return messages


class Patient:
    def __init__(self, patient_id, diagnosis, medical_history):
        self.patient_id = patient_id
        self.diagnosis = diagnosis
        self.medical_history = medical_history
        self.priority = self._calculate_priority()

    def _calculate_priority(self):
        priority = 1
        if "повторно" in self.medical_history:
            priority += 1
        return priority


class Hospital:
    def __init__(self):
        self.departments = [
            Department("Кардиология", ["инфаркт", "аритмия"], 20),
            Department("Неврология", ["инсульт", "эпилепсия"], 15),
            Department("Пульмонология", ["пневмония", "хобл"], 18),
            Department("Терапия", ["грипп", "инфекция"], 30)
        ]
        self.diagnosis_to_department = {
            "инфаркт": self.departments[0],
            "аритмия": self.departments[0],
            "инсульт": self.departments[1],
            "эпилепсия": self.departments[1],
            "пневмония": self.departments[2],
            "хобл": self.departments[2],
            "грипп": self.departments[3],
            "инфекция": self.departments[3]
        }
        self.patients = []
        self.occupancy_history = {dept.name: [] for dept in self.departments}
        self.unassigned_patients = {dept.name: 0 for dept in self.departments}
        self.discharged_patients = {dept.name: 0 for dept in self.departments}
        self.dates = []
        self.department_colors = {
            "Кардиология": "orange",
            "Неврология": "blue",
            "Пульмонология": "green",
            "Терапия": "purple"
        }
        self.report_messages = []
        self.total_patients = 0
        self.placed_patients = 0
        self.unplaced_patients = 0

    def _log(self, message):
        print(message)
        self.report_messages.append(message)

    def add_patient(self, patient, current_date):
        self.patients.append(patient)
        self.total_patients += 1
        dept = self.diagnosis_to_department.get(patient.diagnosis)
        success, message = dept.assign_patient(patient, current_date)
        if success:
            self.placed_patients += 1
            self._log(message)
            return True
        self.unplaced_patients += 1
        self.unassigned_patients[dept.name] += 1
        message = f"[{current_date.strftime('%Y-%m-%d')}] Нет доступных коек для пациента {patient.patient_id}, диагноз: {patient.diagnosis}"
        self._log(message)
        return False

    def update_occupancy(self, current_date):
        messages = []
        for dept in self.departments:
            messages.extend(dept.update_beds(current_date))
        return messages

    def record_occupancy(self, current_date):
        for dept in self.departments:
            self.occupancy_history[dept.name].append(dept.get_occupancy_rate(current_date))
            self.discharged_patients[dept.name] = dept.discharged_count
        self.dates.append(current_date)

    def _create_plot(self, data, title, x_label, y_label, filename, plot_type="line"):
        plt.figure(figsize=(10, 6))
        if plot_type == "line":
            for name, values in data.items():
                plt.plot(self.dates, values, label=name, color=self.department_colors[name])
            plt.grid(True, axis='both')
        else:
            depts = list(data.keys())
            values = list(data.values())
            colors = [self.department_colors[dept] for dept in depts]
            plt.bar(depts, values, color=colors)
            plt.grid(True, axis='y')
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        if plot_type == "line":
            plt.legend()
            plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(filename)
        plt.show()
        plt.close()

    def generate_monthly_report(self):
        self._create_plot(
            self.occupancy_history,
            "Занятость отделений во времени",
            "Дата",
            "Процент занятости (%)",
            "занятость_отделений.png",
            "line"
        )

    def generate_unassigned_report(self):
        self._create_plot(
            self.unassigned_patients,
            "Количество неразмещенных пациентов по отделениям",
            "Отделение",
            "Количество неразмещенных пациентов",
            "неразмещенные_пациенты.png",
            "bar"
        )

    def generate_discharged_report(self):
        self._create_plot(
            self.discharged_patients,
            "Количество выписанных пациентов по отделениям",
            "Отделение",
            "Количество выписанных пациентов",
            "выписанные_пациенты.png",
            "bar"
        )

    def save_report(self):
        try:
            with open("отчет_больницы.txt", "w", encoding="utf-8") as f:
                f.write("Отчет о симуляции больницы\n")
                f.write("============================\n\n")
                f.write("Период симуляции: 2025-05-01 по 2025-05-30\n\n")
                f.write("Журнал событий:\n")
                for message in self.report_messages:
                    f.write(message + "\n")
                f.write("\nИтоги:\n")
                f.write(f"Всего поступило пациентов: {self.total_patients}\n")
                f.write(f"Всего размещено пациентов: {self.placed_patients}\n")
                f.write(f"Всего неразмещено пациентов: {self.unplaced_patients}\n")
                f.write("\nСтатистика отделений:\n")
                for dept in self.departments:
                    f.write(f"{dept.name}:\n")
                    f.write(f"  Неразмещенные пациенты: {self.unassigned_patients[dept.name]}\n")
                    f.write(f"  Выписанные пациенты: {self.discharged_patients[dept.name]}\n")
        except IOError as e:
            self._log(f"Ошибка записи отчета: {e}")

    def simulate_month(self, start_date):
        current_date = start_date
        end_date = start_date + timedelta(days=30)
        diagnoses = ["инфаркт", "инсульт", "пневмония", "грипп", "аритмия", "эпилепсия", "хобл", "инфекция"]
        medical_histories = ["повторно", "впервые"]
        patient_id = 1

        while current_date <= end_date:
            messages = self.update_occupancy(current_date)
            for message in messages:
                self._log(message)

            num_patients = random.randint(0, 15)
            for _ in range(num_patients):
                patient = Patient(
                    f"П{patient_id:03d}",
                    random.choice(diagnoses),
                    random.choice(medical_histories)
                )
                self.add_patient(patient, current_date)
                patient_id += 1

            self.record_occupancy(current_date)

            current_date += timedelta(days=1)

        self.generate_monthly_report()
        self.generate_unassigned_report()
        self.generate_discharged_report()
        self.save_report()
        return ("Симуляция завершена. Графики сохранены как 'занятость_отделений.png', "
                "'неразмещенные_пациенты.png' и 'выписанные_пациенты.png'. "
                "Отчет сохранен как 'отчет_больницы.txt'")


if __name__ == "__main__":
    hospital = Hospital()
    start_date = datetime(2025, 5, 1)
    print(hospital.simulate_month(start_date))