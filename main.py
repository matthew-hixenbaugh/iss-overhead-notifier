import requests
from datetime import datetime, timezone
import smtplib
import time


MY_LAT = 38.7946
MY_LNG = 106.5348

MY_EMAIL = "test@gmail.com"
MY_PASSWORD = "app-generated-password-goes-here"

REFRESH_TIME = 60


class ISSNotifier:

    def __init__(self):
        self.data_handler = ISSDataHandler(self)

        while True:
            self.main_loop()
            time.sleep(REFRESH_TIME)

    def is_iss_near_me(self) -> bool:
        (iss_x, iss_y) = self.data_handler.get_iss_coordinates()
        (my_x, my_y) = self.data_handler.get_my_coordinates()

        if (abs(iss_x - my_x) < 6) & (abs(iss_y - my_y) < 6):
            return True
        else:
            return False

    def is_iss_visible(self) -> bool:
        (my_h, my_m) = self.data_handler.get_my_time()
        (sunrise_h, sunrise_m) = self.data_handler.get_sunrise_time()
        (sunset_h, sunset_m) = self.data_handler.get_sunset_time()

        if (my_h < sunrise_h) | (my_h > sunset_h):
            return True
        elif (my_h == sunrise_h) & (my_m < sunrise_m):
            return True
        elif (my_h == sunset_h) & (my_m > sunset_m):
            return True
        else:
            return False

    @staticmethod
    def send_email_notification():
        smtp_domain = "smtp.google.com"
        email_body = ("Look up! The ISS is currently within 5 degrees of both your latitude and longitude location. "
                      "Additionally, you should be able to see clearly since it is between dusk and dawn!")

        with smtplib.SMTP(smtp_domain) as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(from_addr=MY_EMAIL,
                                to_addrs="ilovetheISS@gmail.com",
                                msg=f"The ISS is Above!\n\n{email_body}")

    def main_loop(self):
        self.data_handler.update()

        print(f"my coords: {self.data_handler.get_my_coordinates()} \n"
              f"my time: {self.data_handler.get_my_time()} \n"
              f"iss coords: {self.data_handler.get_iss_coordinates()} \n"
              f"sunrise time: {self.data_handler.get_sunrise_time()} \n"
              f"sunset time: {self.data_handler.get_sunset_time()}")
        print(f"is the ISS near me? {self.is_iss_near_me()} \n"
              f"is the ISS visible? {self.is_iss_visible()}")

        if self.is_iss_visible() and self.is_iss_near_me():
            self.send_email_notification()
            print("Email sent!")
        else:
            print("No email sent.")


class ISSDataHandler:

    def __init__(self, notifier: ISSNotifier):
        self.notifier = notifier

        self.my_lat = MY_LAT
        self.my_lng = MY_LNG
        self.hour_minute = self.set_datetime_hour_minute()
        self.iss_location = self.set_iss_location()
        [self.sunrise_hour_minute, self.sunset_hour_minute] = self.set_sunrise_sunset_hour_minute()

    def update(self):
        self.hour_minute = self.set_datetime_hour_minute()
        self.iss_location = self.set_iss_location()
        [self.sunrise_hour_minute, self.sunset_hour_minute] = self.set_sunrise_sunset_hour_minute()

    @staticmethod
    def set_datetime_hour_minute() -> list[int]:
        time_now = datetime.now(timezone.utc)
        time_now_hm = [time_now.hour, time_now.minute]
        return time_now_hm

    @staticmethod
    def set_iss_location() -> list[float]:
        response = requests.get(url="http://api.open-notify.org/iss-now.json")
        response.raise_for_status()

        data = response.json()
        iss_current_location = [float(data["iss_position"]["longitude"]), float(data["iss_position"]["latitude"])]
        return iss_current_location

    @staticmethod
    def set_sunrise_sunset_hour_minute() -> list[list[int]]:
        parameters = {
            "lat": MY_LAT,
            "lng": MY_LNG,
            "formatted": 0,
        }
        response = requests.get(url="https://api.sunrise-sunset.org/json", params=parameters)
        response.raise_for_status()

        sunrise = response.json()["results"]["sunrise"]
        sunrise_hms = sunrise.split("T")[1].split(":")
        sunrise_hm = [int(sunrise_hms[0]), int(sunrise_hms[1])]

        sunset = response.json()["results"]["sunset"]
        sunset_hms = sunset.split("T")[1].split(":")
        sunset_hm = [int(sunset_hms[0]), int(sunset_hms[1])]

        return [sunrise_hm, sunset_hm]

    def get_my_coordinates(self) -> list[float]:
        return [self.my_lat, self.my_lng]

    def get_my_time(self) -> list[int]:
        return self.hour_minute

    def get_iss_coordinates(self) -> list[float]:
        return self.iss_location

    def get_sunrise_time(self) -> list[int]:
        return self.sunrise_hour_minute

    def get_sunset_time(self) -> list[int]:
        return self.sunset_hour_minute


def main():
    ISSNotifier()


if __name__ == '__main__':
    main()
