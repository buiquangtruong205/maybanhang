import paho.mqtt.publish as publish
import os

def send_dispense_command(slot_code):
    """
    Gửi lệnh nhả hàng tới máy qua MQTT để phản hồi ngay lập tức.
    """
    try:
        # Lấy cấu hình từ môi trường hoặc mặc định
        broker = os.environ.get('MQTT_BROKER', 'mqtt')
        port = int(os.environ.get('MQTT_PORT', 1883))
        topic = 'vending/v3/machine/3/cmd'
        payload = f"DISPENSE:{slot_code}"
        
        # Publish một tin nhắn duy nhất
        publish.single(
            topic, 
            payload=payload, 
            hostname=broker,
            port=port
        )
        print(f"📡 MQTT: Published dispense command for slot {slot_code} to topic {topic}")
        return True
    except Exception as e:
        print(f"❌ MQTT Error: {str(e)}")
        return False
