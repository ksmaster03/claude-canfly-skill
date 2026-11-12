import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// The reflection/glow layers redraw the stage through CSS filters, so frames
// are expensive; 2 keeps memory flat on this machine.
Config.setConcurrency(2);
