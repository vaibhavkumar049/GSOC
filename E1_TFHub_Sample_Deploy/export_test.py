import tensorflow as tf
import tensorflow_hub as hub
import unittest
import tempfile
import os
from absl.testing import absltest
import export
from export import train_and_export

TMPDIR = tempfile.mkdtemp()
model = None


def load_model(path):
  global model
  if not model:
    model = hub.load(path)
  return model


class TFHubMNISTTest(tf.test.TestCase):
  def setUp(self):
    file_ = tf.gather(tf.io.matching_files("test_data/*.jpg"), 0)
    self.test_image = tf.expand_dims(
        tf.image.decode_jpeg(
            tf.io.read_file(file_)), 0)
    self.test_label = int(str(file_.numpy()).split("/")[-1].split(".jpg")[0])

  def test_model_exporting(self):
    mocked_dict = export.sys.__dict__.copy()
    devnull = open(os.devnull, "w")
    mocked_dict["stdout"] = devnull
    absltest.mock.patch.dict(
        export.sys.__dict__,
        mocked_dict,
        clear=True).start()
    train_and_export(epoch=1, export_path="%s/model/1" % TMPDIR)
    self.assertTrue(os.listdir(TMPDIR))

  def test_model_loadable(self):
    if not os.path.exists("%s/model/1" % TMPDIR):
      self.test_model_exporting()
    model = load_model("%s/model/1" % TMPDIR)
    output_ = model.call(
        tf.zeros([1, 28, 28, 1], dtype=tf.uint8).numpy())
    self.assertEqual(output_.shape, [1, 10])

  def test_model_working(self):
    if not os.path.exists(os.path.join(TMPDIR, "model/1")):
      self.test_model_exporting()
    model = load_model("%s/model/1" % TMPDIR)
    prediction = model.call(self.test_image)
    self.assertEqual(
        tf.argmax(
            tf.squeeze(prediction)).numpy(),
        self.test_label)


if __name__ == '__main__':
  tf.test.main()