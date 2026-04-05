import cv2
from pyzbar.pyzbar import decode
from crypto_utils import decrypt_data
import json
import time

def scan_qr():
    cap = cv2.VideoCapture(0)

    while True:
        _, frame = cap.read()
        decoded = decode(frame)

        for obj in decoded:
            encrypted_data = obj.data.decode()
            try:
                decrypted = decrypt_data(encrypted_data)
                data = json.loads(decrypted)

                username = data["user"]
                timestamp = data["timestamp"]

                # Check expiry (30 sec)
                if time.time() - timestamp < 30:
                    print(f"✅ Authenticated: {username}")
                else:
                    print("❌ QR expired")

                cap.release()
                cv2.destroyAllWindows()
                return

            except:
                print("❌ Invalid QR")

        cv2.imshow("Scan QR", frame)

        if cv2.waitKey(1) == 27:
            break

scan_qr()