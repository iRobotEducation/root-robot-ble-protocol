#!/usr/bin/env python3

import gatt
import threading

# BLE UUID's
root_identifier_uuid = '48c5d828-ac2a-442d-97a3-0c9822b04979'
uart_service_uuid = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
tx_characteristic_uuid = '6e400002-b5a3-f393-e0a9-e50e24dcca9e' # Write
rx_characteristic_uuid = '6e400003-b5a3-f393-e0a9-e50e24dcca9e' # Notify

class BluetoothDeviceManager(gatt.DeviceManager):
    robot = None # root robot device

    def device_discovered(self, device):
        print("[%s] Discovered: %s" % (device.mac_address, device.alias()))
        self.stop_discovery() # Stop searching
        self.robot = RootDevice(mac_address=device.mac_address, manager=self)
        self.robot.connect()

class RootDevice(gatt.Device):
    def services_resolved(self):
        super().services_resolved()
        print("[%s] Resolved services" % (self.mac_address))

        self.uart_service = next(
            s for s in self.services
            if s.uuid == uart_service_uuid)

        self.tx_characteristic = next(
            c for c in self.uart_service.characteristics
            if c.uuid == tx_characteristic_uuid)

        self.rx_characteristic = next(
            c for c in self.uart_service.characteristics
            if c.uuid == rx_characteristic_uuid)

        self.rx_characteristic.enable_notifications() # listen to RX messages

    def characteristic_value_updated(self, characteristic, value):
        message = []
        for byte in value:
            message.append(byte)
        print(message)

    def drive_forward(self):
        self.tx_characteristic.write_value([0x01, 0x04, 0x00, 0x00, 0x00, 0x00,
            0x64, 0x00, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xD1])


# start here if run as program / not imported as module
if __name__ == "__main__":

    manager = BluetoothDeviceManager(adapter_name = 'hci0')
    manager.start_discovery(service_uuids=[root_identifier_uuid])
    thread = threading.Thread(target = manager.run)
    thread.start()

    try:
        while manager.robot is None:
            pass # wait for a root robot to be discovered

        print("Press Enter to drive robot, CTRL-C to quit")

        while True:
            input() # wait for keyboard input
            manager.robot.drive_forward()

    except KeyboardInterrupt:
        print("\tCTRL-C pressed")
        manager.stop()
        manager.robot.disconnect()
        thread.join()
