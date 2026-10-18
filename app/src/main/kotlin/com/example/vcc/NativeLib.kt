package com.example.vcc

class NativeLib {
    external fun stringFromJNI(): String

    companion object {
        init {
            System.loadLibrary("native-lib")
        }
    }
}
