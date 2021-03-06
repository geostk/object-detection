import os
import sys
import importlib
from dataset.pascal_voc import PascalVoc
from dataset.custom import Custom
from dataset.iterator import DetIter
from dataset.iterator_kaist import DetIterKAIST
from dataset.iterator_cvc import DetIterCVC
from detect.detector import Detector
from detect.detector_kaist import DetectorKAIST
from detect.detector_cvc import DetectorCVC
from config.config import cfg
import logging

def evaluate_net(network_name,
                 dataset,
                 dataset_path,
                 mean_pixels,
                 data_shape,
                 model_prefix,
                 epoch,
                 ctx,
                 mode='rgb',
                 year=None,
                 sets='test',
                 batch_size=1,
                 nms_thresh=0.5,
                 force_nms=False):
    """
    Evaluate entire dataset, basically simple wrapper for detections

    Parameters:
    ---------
    dataset : str
        name of dataset to evaluate
    devkit_path : str
        root directory of dataset
    mean_pixels : tuple of float
        (R, G, B) mean pixel values
    data_shape : int
        resize input data shape
    model_prefix : str
        load model prefix
    epoch : int
        load model epoch
    ctx : mx.ctx
        running context, mx.cpu() or mx.gpu(0)...
    year : str or None
        evaluate on which year's data
    sets : str
        evaluation set
    batch_size : int
        using batch_size for evaluation
    nms_thresh : float
        non-maximum suppression threshold
    force_nms : bool
        force suppress different categories
    """
    # set up logger
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if dataset == "pascal":
        if not year:
            year = '2007'
        imdb = PascalVoc(sets, year, dataset_path, shuffle=False, is_train=False)
        data_iter = DetIter(imdb, batch_size, data_shape, mean_pixels, rand_samplers=[], rand_mirror=False, is_train=False, shuffle=False)
        sys.path.append(os.path.join(cfg.ROOT_DIR, 'symbol'))

        if network_name == 'vgg16_reduced':
            net = importlib.import_module('symbol_' + network_name).get_symbol(imdb.num_classes, nms_thresh, force_nms)
        else:
            net = importlib.import_module('get_symbol').get_symbol(imdb.num_classes, nms_thresh, force_nms,  network_name)

        model_prefix += "_" + str(data_shape)
        detector = Detector(net, model_prefix, epoch, data_shape, mean_pixels, batch_size, ctx)
        logger.info("Start evaluation with {} images, be patient...".format(imdb.num_images))
        detections = detector.detect(data_iter)
        imdb.evaluate_detections(detections)

    elif dataset == 'kaist':
        imdb = Custom(sets, dataset_path, shuffle=False, is_train=False)
        mean_rgb = [123, 117, 104]
        std_rgb = [65.1171282799, 62.1827802828, 61.1897309395]
        mean_tir = [42.6318449296]
        std_tir = [27.2190767513]

        data_iter = DetIterKAIST(imdb, batch_size, data_shape,  mean_rgb,
                                  std_rgb,
                                  mean_tir,
                                  std_tir, rand_samplers=[], rand_mirror=False, is_train=False, shuffle=False)
        sys.path.append(os.path.join(cfg.ROOT_DIR, 'symbol'))
        net = importlib.import_module('get_symbol').get_symbol(imdb.num_classes, nms_thresh, force_nms,  network_name)
        model_prefix += "_" + str(data_shape)
        detector = DetectorKAIST(net, model_prefix, epoch, data_shape, mean_pixels, batch_size, ctx)
        logger.info("Start evaluation with {} images, be patient...".format(imdb.num_images))
        detections = detector.detect(data_iter)
        imdb.evaluate_detections(detections)

    elif dataset == 'cvc':
        imdb = Custom(sets, dataset_path, shuffle=False, is_train=False)
        data_iter = DetIterCVC(imdb, batch_size, data_shape, mean_pixels, rand_samplers=[], rand_mirror=False, is_train=False, shuffle=False)
        sys.path.append(os.path.join(cfg.ROOT_DIR, 'symbol'))
        net = importlib.import_module('get_symbol').get_symbol(imdb.num_classes, nms_thresh, force_nms,  network_name)
        model_prefix += "_" + str(data_shape)
        detector = DetectorCVC(net, model_prefix, epoch, data_shape, mean_pixels, batch_size, ctx)
        logger.info("Start evaluation with {} images, be patient...".format(imdb.num_images))
        detections = detector.detect(data_iter)
        imdb.evaluate_detections(detections)

    else:
        raise NotImplementedError, "No support for dataset: " + dataset
