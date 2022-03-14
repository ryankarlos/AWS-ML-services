import os
import random
import tensorflow as tf
import tensorflow_datasets as tfds
import shutil

print(f"GPU Available: {tf.config.experimental.list_physical_devices('GPU')} \n")


def download_tfds_dataset(name, dir, shuffle=True):
    return tfds.load(
        name,
        split=["train[:0.5%]", "test[0:0.5%]"],
        shuffle_files=shuffle,
        data_dir=dir,
    )


def create_sample_images_from_dir(
    labels: list,
    number_of_samples: int,
    cropped_dim: tuple,
    images_dir: str,
    samples_dir: str,
):
    builder = tfds.ImageFolder(images_dir)
    dataset = builder.as_dataset(split="train", shuffle_files=True, as_supervised=True)
    label_map = builder.info.features["label"]
    delete_image_folders(samples_dir)
    for label in labels:

        folder_path = os.path.join(samples_dir, label)
        os.mkdir(folder_path)
        dataset_filtered = dataset.filter(
            lambda x, y: tf.equal(y, label_map.str2int(label))
        ).take(number_of_samples)
        for image, _ in dataset_filtered:
            cropped = tf.image.resize_with_crop_or_pad(
                image, cropped_dim[0], cropped_dim[1]
            )
            enc = tf.image.encode_jpeg(cropped)
            fname = tf.constant(f"{folder_path}/{random.randint(0, 20000)}.jpeg")
            fwrite = tf.io.write_file(fname, enc)
        print(f"Completed writing samples for {label} images")


def delete_image_folders(samples_dir):
    folder_list = os.listdir(samples_dir)
    if folder_list:
        print(f"Deleting image folders: {','.join(folder_list)} from {samples_dir}")
        for file in folder_list:
            folder_path = os.path.join(samples_dir, file).replace("\\", "/")
            shutil.rmtree(folder_path)
        print(f"Deletion complete !")
    else:
        print(f"Folder {samples_dir} is empty. No files to be deleted")


if __name__ == "__main__":
    # download_tfds_dataset("food101", r"food-cv" )
    labels = ["apple_pie", "chocolate_cake", "fish_and_chips", "pizza"]
    samples = 20
    crop_dim = (400, 400)
    samples_dir = "cv/food101/samples/"
    images_dir = "cv/food101/"
    create_sample_images_from_dir(labels, samples, crop_dim, images_dir, samples_dir)
