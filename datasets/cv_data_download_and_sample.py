import os
import random
import tensorflow as tf
import tensorflow_datasets as tfds
import shutil
import logging
from tqdm import tqdm
from dask import delayed
import argparse

print(f"GPU Available: {tf.config.experimental.list_physical_devices('GPU')} \n")
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s:%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def download_tfds_dataset(name, dir, shuffle=True):
    return tfds.load(
        name,
        split=["train[:0.5%]", "test[0:0.5%]"],
        shuffle_files=shuffle,
        data_dir=dir,
    )


def sample_images_for_aws(
    labels: list,
    number_of_samples: int,
    cropped_dim: tuple,
    images_dir: str,
    samples_dir: str,
):
    delete_image_folders(samples_dir)
    pbar1 = tqdm(labels)
    for label in pbar1:
        pbar1.set_description(f"Writing images for label {label}")
        dataset_filtered, folder_path = filter_raw_images_from_local_folder(
            images_dir, label, number_of_samples
        )
        pbar2 = tqdm(dataset_filtered)
        for image, _ in pbar2:
            fname = tf.constant(f"{folder_path}/{random.randint(0, 200000)}.jpeg")
            pbar2.set_description(f"Resizing and writing {fname}")
            fwrite = resize_and_write_images(image, fname, cropped_dim)
            fwrite.compute()
        logger.info(f"Completed writing food101_aws for {label} images")


def filter_raw_images_from_local_folder(images_dir, label, number_of_samples):
    builder = tfds.ImageFolder(images_dir)
    dataset = builder.as_dataset(split="train", shuffle_files=True, as_supervised=True)
    label_map = builder.info.features["label"]
    folder_path = os.path.join(samples_dir, label)
    os.mkdir(folder_path)
    dataset_filtered = dataset.filter(
        lambda x, y: tf.equal(y, label_map.str2int(label))
    ).take(number_of_samples)
    return dataset_filtered, folder_path


@delayed
def resize_and_write_images(image, fname, cropped_dim):
    cropped = tf.image.resize_with_crop_or_pad(image, cropped_dim[0], cropped_dim[1])
    enc = tf.image.encode_jpeg(cropped)
    return tf.io.write_file(fname, enc)


def delete_image_folders(samples_dir):
    folder_list = os.listdir(samples_dir)
    if folder_list:
        logger.info(
            f"Deleting image folders: {','.join(folder_list)} from {samples_dir}"
        )
        for file in folder_list:
            folder_path = os.path.join(samples_dir, file).replace("\\", "/")
            shutil.rmtree(folder_path)
        logger.info(f"Deletion complete !")
    else:
        logger.info(f"Folder {samples_dir} is empty. No files to be deleted")


def add_arguments(parser):
    """
    Adds command line arguments to the parser.
    :param parser: The command line parser.
    """

    parser.add_argument(
        "--labels", help="List of labels to be used e.g. ['apple_pie', 'chocolate_cake', 'fish_and_chips', 'pizza']"
    )
    parser.add_argument("--samples", default=250, help="Number of random samples to use for AWS upload from raw data")
    parser.add_argument(
        "--crop_dim", default=(400,400), help="Dimensions to resize the images"
    )

    parser.add_argument("--samples_dir", help="local dir where the samples for aws will be stored")
    parser.add_argument(
        "--images_dir", help="dir where the raw images downloaded from tf datasets"
    )


def main():
    # get command line arguments
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    add_arguments(parser)
    args = parser.parse_args()
    # download_tfds_dataset("food101", r"food-cv" )
    sample_images_for_aws(args.labels, args.samples, args.crop_dim, args.images_dir, args.samples_dir)


if __name__ == "__main__":
    main()