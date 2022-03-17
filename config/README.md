
The script cv_data_download_and_sample.py can be run to download any of the available tensoflow datasets
https://blog.tensorflow.org/2019/02/introducing-tensorflow-datasets.html
Alternatively, we can also sample some of the data we have in local folder tree to generate smaller
samples for testing on AWS (e.g. few classes and data per class with resized/cropped dim images)

The  params samples,crop_dim, samples_dir(filtered with fewer images/labels), images_dir (raw images dir tree to be sampled from) need to be set appropriately
With the default settings, you should get the following output

```
E:\AWS-automl\venv\Scripts\python.exe E:/AWS-automl/datasets/cv_data_download_and_sample.py
GPU Available: [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')] 

2022-03-14 18:56:32.526728: I tensorflow/core/platform/cpu_feature_guard.cc:151] This TensorFlow binary is optimized with oneAPI Deep Neural Network Library (oneDNN) to use the following CPU instructions in performance-critical operations:  AVX AVX2
To enable them in other operations, rebuild TensorFlow with the appropriate compiler flags.
2022-03-14 18:56:32.840350: I tensorflow/core/common_runtime/gpu/gpu_device.cc:1525] Created device /job:localhost/replica:0/task:0/device:GPU:0 with 7446 MB memory:  -> device: 0, name: NVIDIA GeForce RTX 3080, pci bus id: 0000:0b:00.0, compute capability: 8.6
Deleting image folders: apple_pie,chocolate_cake,fish_and_chips,pizza from cv/food101/samples/
Deletion complete !
Completed writing samples for apple_pie images
Completed writing samples for chocolate_cake images
Completed writing samples for fish_and_chips images
Completed writing samples for pizza images

Process finished with exit code 0
```