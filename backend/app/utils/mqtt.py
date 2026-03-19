import paho.mqtt.publish as publish
import os

def send_dispense_command(machine_id, slot_code):
    """
    Gửi lệnh nhả hàng tới máy qua MQTT để phản hồi ngay lập tức.
    """
    try:
        # Lấy cấu hình từ môi trường hoặc mặc định
        broker = os.environ.get('MQTT_BROKER', 'mqtt')
        port = int(os.environ.get('MQTT_PORT', 1883))
        # Build dynamic topic: vending/v3/machine/<machine_id>/cmd
        topic = f"vending/v3/machine/{machine_id}/cmd"
        payload = f"DISPENSE:{slot_code}"
        
        # Publish một tin nhắn duy nhất
        publish.single(
            topic, 
            payload=payload, 
            hostname=broker,
            port=port
        )
        print(f"📡 MQTT: Published dispense command for machine {machine_id}, slot {slot_code} to topic {topic}")
        return True
    except Exception as e:
        print(f"❌ MQTT Error: {str(e)}")
        return False


def send_machine_command(machine_id, cmd, val=""):
    """
    Gửi lệnh điều khiển hệ thống tới máy qua MQTT (REBOOT, RESET_CONFIG, TEST_MOTOR).
    """
    try:
        broker = os.environ.get('MQTT_BROKER', 'mqtt')
        port = int(os.environ.get('MQTT_PORT', 1883))
        topic = f"vending/v3/machine/{machine_id}/cmd"
        
        payload = f"{cmd}:{val}" if val else cmd
        
        publish.single(
            topic, 
            payload=payload, 
            hostname=broker,
            port=port
        )
        print(f"📡 MQTT: Published command {payload} for machine {machine_id} to topic {topic}")
        return True
    except Exception as e:
        print(f"❌ MQTT Error: {str(e)}")
        return False
