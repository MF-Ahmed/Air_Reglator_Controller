/*
  Analog input, analog output, serial output

  Reads an analog input pin, maps the result to a range from 0 to 255 and uses
  the result to set the pulse width modulation (PWM) of an output pin.
  Also prints the results to the Serial Monitor.

  The circuit:
  - potentiometer connected to analog pin 0.
    Center pin of the potentiometer goes to the analog pin.
    side pins of the potentiometer go to +5V and ground
  - LED connected from digital pin 9 to ground

  created 29 Dec. 2008
  modified 9 Apr 2012
  by Tom Igoe

  This example code is in the public domain.

  http://www.arduino.cc/en/Tutorial/AnalogInOutSerial
*/

// These constants won't change. They're used to give names to the pins used:
const int analogInPin1 = A0;  // Analog input pin that the potentiometer is attached to
const int analogInPin2 = A1;  // Analog input pin that the potentiometer is attached to
const int analogInPin3 = A2;  // Analog input pin that the potentiometer is attached to
const int analogInPin4 = A3;  // Analog input pin that the potentiometer is attached to

const int analogOutPin = 9; // Analog output pin that the LED is attached to

int sensorValue1 = 0;        // value read from the pot
int sensorValue2 = 0;        // value read from the pot
int sensorValue3 = 0;        // value read from the pot
int sensorValue4 = 0;        // value read from the pot

char outputValueS1_LB = 0;        // value output to the PWM (analog out)
char outputValueS1_HB = 0;        // value output to the PWM (analog out)

void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(9600);
}

void loop() {
  // read the analog in value:
  sensorValue1 = analogRead(analogInPin1);
  sensorValue1 = sensorValue1*10;
  sensorValue2 = analogRead(analogInPin2);
  sensorValue2 = sensorValue2*10;
  sensorValue3 = analogRead(analogInPin3);
  sensorValue3 = sensorValue3*10;

  
  //sensorValue1 = 0x00AA;
  // map it to the range of the analog out:
  
  sensorValue1 = map(sensorValue1, 0, 1023, 0, 100);
  sensorValue2 = map(sensorValue2, 0, 1023, 0, 26);
  sensorValue3 = map(sensorValue3, 0, 1023, 0, 250);
  
  //outputValueS1_HB = map(sensorValue1, 0, 1023, 0, 255);
  // change the analog out value:
  //analogWrite(analogOutPin, outputValue);

  // print the results to the Serial Monitor:
  Serial.write(0xAA);
  Serial.write(0x55);

  Serial.write(0x33);
  
  Serial.write(sensorValue1>>8);
  Serial.write(sensorValue1);
  
  Serial.write(sensorValue2>>8);
  Serial.write(sensorValue2);
  
  Serial.write(sensorValue3>>8);
  Serial.write(sensorValue3);


  Serial.write(0x01);
  Serial.write(0x01);

  //Serial.print("\n\r");
  //Serial.println(sensorValue);
  //Serial.print("\t output = ");
  //Serial.println(outputValue);

  // wait 2 milliseconds before the next loop for the analog-to-digital
  // converter to settle after the last reading:
  delay(100);
}
